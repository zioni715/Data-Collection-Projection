# 3_Event_Contract_and_Versioning.md
이 단계는 **센서(OS/Add-in) ↔ 코어(collector)** 사이의 “이벤트 계약(Contract)”을 고정하고, 이후 스펙 변경에도 깨지지 않도록 **버전/호환성**을 설계하는 단계입니다.  
(실제 구현은 3~6단계 어디서든 병행 가능하지만, *빨리 고정할수록* 전체 개발이 편해집니다.)

---

## 목표
- 모든 이벤트가 **한 가지 공통 Envelope**로 들어오도록 강제
- 이벤트 타입/필드가 늘어나도 **구버전 수신**이 깨지지 않게 설계
- Sensor가 제각각 보내도 코어가 **검증/정규화/거절**할 수 있게 만들기

---

## 해야 할 일(체크리스트)

### 1) 공통 Envelope v1 확정
필수 필드(최소):
- `schema_version` (예: `"1.0"`)
- `event_id`, `ts`
- `source`, `app`, `event_type`
- `pid`, `window_id`(원문 허용 여부는 정책으로)
- `resource {type,id}`
- `payload {}`
- `privacy {pii_level, redaction[]}`
- `priority` (P0/P1/P2)

**산출물**
- `schemas/event.schema.json` 업데이트(버전 필드 포함)
- `collector/models.py`에 version 필드 추가(또는 metadata)

### 2) event_type 네이밍 규칙 정의
권장 규칙(예시):
- OS: `os.foreground_changed`, `os.app_focus_block`, `os.idle_start`, `os.file_changed`
- Excel: `excel.refresh_pivot`, `excel.export_pdf`
- Outlook: `outlook.send_clicked`, `outlook.compose_started`

**산출물**
- `docs/event_types.md` 또는 `schemas/event_types.yaml` (명세 목록)

### 3) payload “가변 필드” 정책
- payload는 이벤트별로 달라질 수 있으므로 **스키마 검증을 완화**하되,
- 공통적으로 민감 가능성이 있는 문자열 필드(예: window_title)는 **규칙적으로 마스킹 대상**으로 명시

**산출물**
- `configs/privacy_rules.yaml`에 “마스킹 대상 키 목록” 추가(예: `window_title`, `url`, `path` 등)

### 4) 호환성 전략(Forward/Backward)
- 코어는 `schema_version`을 보고:
  - 낮은 버전: 가능한 필드만 읽고 나머지 기본값 채움
  - 높은 버전: **모르는 필드는 무시**하되, 핵심 필드 없으면 거절

**산출물**
- `normalize.py`에 “버전별 fallback” 규칙 반영(문서화라도 먼저)

### 5) 검증 레벨(Validation level) 정하기
- Strict 모드: 필수 필드 없으면 drop + error log
- Lenient 모드: 필수 필드만 채우고 나머지 무시

**권장**
- 개발 초기: Lenient(빠르게 흐름 만들기)
- 운영 단계: Strict(이상 이벤트 차단)

---

## 완료 기준
- [ ] 센서/수신기에서 어떤 JSON이 오더라도 코어가 Envelope로 맞추거나 거절할 수 있다
- [ ] schema_version 변경이 들어와도 코어가 “깨지지 않고” 처리한다(최소 무시/드롭)
- [ ] event_type 목록/규칙이 문서로 고정되어 팀 내 합의가 끝났다
