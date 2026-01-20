# Data Collection Architecture (OS + Add-in Hybrid)
**Scope:** From local sensors to *handoff package* 전달(= Local Super Agent에게 넘기기 직전)까지의 **데이터 수집/가공 아키텍처**  
**Out of scope:** 추천 문구 생성, 사용자 동의(yes/no) 처리, n8n 워크플로 생성/실행

---

## 1. 목표와 원칙

### 목표
- 로컬 PC에서 사용자의 업무 흐름을 **넓게(OS)** 수집하고, 가능 앱은 **깊게(Add-in/Extension)** 수집
- 원시 로그를 그대로 남기지 않고 **경량화(압축/샘플링/우선순위)** 하여 저장 비용 절감
- 개인정보/보안 리스크를 줄이기 위해 **내용(content) 수집 최소화** + **비식별화/토큰화**
- 자동화 후보 탐지에 필요한 **세션/루틴 후보**를 생성하여 Super Agent에 전달

### 설계 원칙
- **OS는 “흐름(앱/창/시간/파일)”**, Add-in은 “의미(피벗/발송/내보내기 등)”를 담당
- 변경분만 기록하고, 노이즈는 **Debounce/Block 압축**으로 제거
- 민감정보(경로/수신자/제목 등)는 **해시/마스킹**이 기본값
- 장기 보관은 **요약/루틴 정의** 중심, Raw는 단기 보관

---

## 2. 전체 파이프라인 (Local Super Agent 전달 전까지)

```text
[OS Sensor]      [Add-in/Extension Sensors]
     |                  |
     +-----> ① Event Ingest (IPC)  <-----+
                    |
                ② Normalizer
                    |
                ③ Privacy Guard
                    |
                ④ Prioritizer & Sampler
                    |
                ⑤ Local Event Store (SQLite)
                    |
                ⑥ Session Builder
                    |
                ⑦ Summary/Feature Builder
                    |
                ⑧ Routine Candidate Builder
                    |
                ⑨ Handoff Queue (to Local Super Agent)
```

- **⑤까지:** 이벤트 원장(Ledger) + 압축(block) 저장
- **⑥~⑧:** 세션/요약/루틴 후보 생성(의미 단위)
- **⑨:** Super Agent가 소비하는 *최소 입력* 패키지 생성

---

## 3. Sensor 설계

### 3.1 OS Sensor (넓고 얕게: baseline coverage)
**목적:** 앱 간 이동/시간 블록/파일 흔적을 통해 *세션 뼈대*를 만들기

#### 권장 이벤트 (최소 세트)
- `foreground_app_changed` : 포그라운드 앱 변경
- `foreground_window_changed` : 활성 창 변경(제목은 마스킹/길이 제한)
- `idle_start`, `idle_end` : 유휴 시작/종료(세션 경계)
- `file_event` : 생성/수정/이동/삭제(파일 watcher 기반)
- (선택) `process_start`, `process_exit`
- (선택) `download_completed_meta` : 다운로드 완료(메타)
- (선택) `clipboard_changed_meta` : 클립보드 변경(타입/길이만)

#### 리소스 절약(필수)
- **Polling은 0.5~1초**로 하되, *상태가 변할 때만* 이벤트 생성
- **Debounce:** 2초 미만의 초단기 전환은 기록하지 않음(노이즈 컷)
- **Focus block 압축:** 동일 앱/창 상태 유지 시 이벤트를 누적하여 1개 레코드로 저장  
  예) `app_focus_block(duration=180s, app=EXCEL, window_id=...)`

---

### 3.2 Add-in/Extension Sensors (좁고 깊게: semantic events)
**목적:** OS로는 알기 어려운 “앱 내부 의미 이벤트”를 확정

#### Excel Add-in 예시
- `workbook_opened`
- `refresh_pivot`, `refresh_query`
- `filter_applied`, `sort_applied`
- `export_pdf`, `export_csv`
- `chart_copied`
- `save_as`

> 기본값: 셀 값/본문 등 **content 수집 금지**. 필요 시 로컬 요약 후 특징만 저장.

#### Outlook Add-in 예시
- `compose_started`
- `attachment_added_meta` : (확장자/용량/개수)
- `recipients_selected_meta` : (해시/그룹ID)
- `send_clicked` : **강력한 종결 이벤트**(세션 종료 트리거)

#### Browser Extension(선택)
- `tab_activated`
- `domain_changed`
- `download_completed_meta`
> URL 전체/페이지 내용 수집은 피하고 **도메인/경로 일부 + 메타** 중심

---

## 4. Event Ingest (Sensor → Core) 인터페이스

### 4.1 권장 통신 방식
- 동일 PC 내부 IPC: **Named Pipe / Unix Domain Socket / local gRPC** 등
- Sensor는 이벤트를 “발행(publish)”만, Core가 “정규화/보호/저장”을 전담

### 4.2 Ingest 최소 책임
- timestamp 표준화(UTC)
- `source_id` 부여(os/excel/outlook/…)
- 중복 방지 `event_id`(UUID) 생성(또는 Sensor가 생성)

---

## 5. Normalizer: 공통 이벤트 스키마

### 5.1 Event Envelope (권장)
```json
{
  "event_id": "uuid",
  "ts": "2026-01-20T10:15:02.120Z",
  "source": "os|excel_addin|outlook_addin|browser_ext",
  "app": "EXCEL|OUTLOOK|CHROME|...",
  "event_type": "app_focus_block|send_clicked|export_pdf|...",
  "pid": 1234,
  "window_id": "hash",
  "resource": {
    "type": "file|email|web",
    "id": "hash",
    "label_local": "optional"
  },
  "payload": {},
  "privacy": {
    "pii_level": "low|med|high",
    "redaction": ["path_hashed", "title_masked"]
  },
  "priority": "P0|P1|P2"
}
```

### 5.2 Resource ID 규칙
- 파일/메일/수신자 등 원본 문자열은 저장하지 않고 `hash(original)` 사용
- 원본 매핑이 필요하면 **로컬 vault**에만 저장(암호화 권장)

---

## 6. Privacy Guard (수집 프로그램의 안전장치)

### 6.1 기본 정책
- **내용(content) 수집 금지:** 메일 본문/문서 본문/셀 값/채팅 내용/키 입력 등
- 창 제목 저장 시:
  - 길이 제한(예: 80자)
  - 이메일/전화/긴 숫자열 패턴 마스킹
- 앱 allowlist/denylist:
  - 은행/비밀번호관리자/개인 메신저 등 기본 deny 권장

### 6.2 PII 등급 가이드
- **Low:** 앱 전환, duration block, 파일 확장자, 첨부 개수
- **Med:** 파일명/창제목(마스킹), 리소스 해시
- **High:** 이메일 주소/수신자/경로 원문 → **해시/토큰화 강제**

---

## 7. Prioritizer & Sampler (경량화 핵심)

### 7.1 우선순위 레벨
- **P0 (절대 보존, 즉시 flush)**  
  - `send_clicked`, `export_pdf`, `file_saved`, `refresh_pivot` 등 “완료/결과” 이벤트
- **P1 (보존, 배치 flush)**  
  - `file_opened`, `compose_started`, 5초 이상 focus block
- **P2 (샘플링/드롭 가능)**  
  - 잦은 window_title 변경, 짧은 탭 전환, clipboard meta 등

### 7.2 드롭/샘플링 규칙(예시)
- 2초 미만 앱 전환 기록하지 않기
- 동일 (app, window_id) 상태 유지 시 이벤트를 누적 → block 1개로 저장
- 버퍼 압박 시 **P2부터 드롭**, P0/P1은 유지

---

## 8. Local Event Store (SQLite 중심)

### 8.1 저장 계층(권장 3계층)
1) **Raw Ledger (단기):** 이벤트 원장(append-only)  
2) **Session Store (중기):** 세션 요약/특징  
3) **Routine Candidate Store (중기~장기):** 반복 후보/점수/근거

### 8.2 테이블 예시

#### `events` (원장)
- `event_id` (PK)
- `ts` (index)
- `source`, `app`, `event_type` (index)
- `priority`
- `pid`, `window_id`
- `resource_type`, `resource_id`
- `payload_json`

#### `focus_blocks` (압축 결과)
- `block_id`
- `start_ts`, `end_ts`
- `app`, `window_id`
- `duration`
- `resource_id` (optional)

#### `vault_resources` (로컬 전용 매핑, 암호화 권장)
- `resource_id` (PK hash)
- `resource_plaintext` (경로/수신자 그룹 등)
- 접근은 Core 내부로 제한

### 8.3 보관 정책(예시)
- Raw events: **7~14일**
- Session summary: **60~90일**
- 확정 루틴(사용자가 “유효” 표시): 장기 보관

---

## 9. Session Builder (업무 단위 만들기)

### 9.1 세션 분할 규칙(실무 기본)
- `idle >= 10~15분`이면 세션 종료
- 강한 종결 이벤트가 있으면 세션 종료 가중치 ↑  
  - `send_clicked`, `export_pdf` 등

### 9.2 결합(Join) 규칙
- Add-in 이벤트 시점 ±2~5초 내 OS 상태(포그라운드 app/window)와 결합
- 동일 `resource_id` 힌트가 있으면 우선 결합

### 9.3 세션 요약 레코드 예시
```json
{
  "session_id": "uuid",
  "start_ts": "...",
  "end_ts": "...",
  "apps_timeline": ["EXCEL(18m)", "OUTLOOK(6m)"],
  "key_events": ["refresh_pivot", "export_pdf", "send_clicked"],
  "resources": ["file:hashA", "file:hashB"],
  "confidence": 0.90
}
```

---

## 10. Summary/Feature Builder (Super Agent용 입력 경량화)

### 10.1 왜 필요한가
- 원장 전체를 넘기면 무겁고 프라이버시 리스크 증가  
- Super Agent는 “추천/의사결정”에 필요한 **요약 특징**만 받는 것이 안정적

### 10.2 세션에서 뽑을 특징(예)
- 앱 순서: `Excel → Outlook`
- 핵심 이벤트 유무: pivot refresh / export / send
- 소요시간, 시간대, 요일
- 연관 리소스(파일/템플릿 해시)
- 반복성 힌트(최근 N일 유사 세션 개수)

---

## 11. Routine Candidate Builder (반복 루틴 후보 생성)

### 11.1 MVP 로직(가벼운 방식)
- 세션의 `key_events` 시퀀스로 n-gram(3~6) 생성 → 빈도 계산
- 주기성(요일/시간대) 점수화
- 결과: “루틴 후보 TOP N”

### 11.2 루틴 후보 스펙 예시
```json
{
  "routine_id": "uuid",
  "pattern": ["refresh_pivot", "export_pdf", "send_clicked"],
  "supports": 6,
  "last_seen": "2026-01-19",
  "time_pattern": { "weekday": "MON", "time_range": "08:00-11:00" },
  "confidence": 0.86,
  "evidence_session_ids": ["s1","s2","s3"]
}
```

---

## 12. Handoff Queue: Local Super Agent에 전달할 패키지

### 12.1 전달 원칙
- **현재 컨텍스트 + 최근 세션 요약 + 루틴 후보 TOP N**만 전달
- 민감 원본(경로/주소/본문)은 넘기지 않음(필요 시 로컬 vault에서만 조회)

### 12.2 Handoff Package 예시
```json
{
  "handoff_id": "uuid",
  "generated_at": "...",
  "recent_context": {
    "active_app": "EXCEL",
    "active_window_masked": "sales_****.xlsx",
    "last_focus_blocks": []
  },
  "recent_sessions": [],
  "routine_candidates": [],
  "privacy_state": {
    "content_collection": false,
    "denylisted_apps_active": false
  }
}
```

---

## 13. 운영/품질 체크리스트

### 13.1 성능/안정성
- In-memory ring buffer + 디스크 스풀(폭주 대비)
- SQLite: WAL 모드 + 배치 insert
- 장애 시 복구: append-only 원장 + 재세션화 가능

### 13.2 보안
- at-rest 암호화(특히 vault)
- 로컬 삭제/보관기간 설정 UI(사용자 제어권)
- denylist 앱 활성 시 수집 즉시 중단

### 13.3 데이터 품질
- 노이즈 컷(짧은 전환/중복 이벤트 제거)
- P0 이벤트는 절대 유실 금지(백압/재시도 설계)

---

## 14. 구현 단위(모듈 분리 권장)
- `os-sensor` : focus/app/window/idle/file watcher
- `addin-excel`, `addin-outlook` : 앱별 의미 이벤트 발행
- `core-agent` : ingest → normalize → privacy → prioritize → store
- `session-service` : session builder + summaries
- `routine-service` : routine candidates 생성
- `handoff-service` : handoff queue 생성/관리

---
