# 4. Core Pipeline MVP
**목표:** 외부에서 “샘플 이벤트 1개”를 넣으면, 코어가 받아서 **SQLite(events)** 에 1행으로 저장되게 만든다.  
(센서 없이도 가능. 가장 먼저 뚫어야 이후 단계가 빨라짐)

---

## 4.1 산출물
- 실행 가능한 `collector` 서비스(프로세스)
- `collector.db` 생성 + `events` 테이블 생성
- 샘플 이벤트 입력 → `events`에 저장 확인

---

## 4.2 작업 순서
### 1) Config 로딩
- `configs/config.yaml`에서 아래만 먼저 확정
  - db_path
  - migrations_path
  - ingest(HTTP receiver on/off, port)
  - privacy(hash_salt는 임시라도 넣기)

**체크:** 실행 시 config 로드 실패 없이 다음 단계로 진행.

### 2) DB 마이그레이션
- `migrations/001_init.sql`에 최소 `events` 테이블 생성
- 실행 시 DB가 없으면 생성, 있으면 스키마 확인

**체크:** `sqlite3 collector.db ".tables"` 에서 events가 보인다.

### 3) Ingest(테스트용) 하나만 열기
- 가장 쉬운 방법: **local HTTP receiver**
- `POST /events`에 JSON(단건/배치)을 받도록 한다

**체크:** curl로 요청이 200 OK.

### 4) 이벤트 파이프라인 최소 루프
- raw event(dict) → normalize → store.insert

**체크:** `select count(*) from events;`가 증가한다.

---

## 4.3 샘플 이벤트 계약(최소)
샘플 입력은 아래 키만 있으면 된다(나머지는 코어가 채움).
- source: "os" | "excel_addin" | ...
- app: "EXCEL" | "OUTLOOK" | "CHROME" | ...
- event_type: "app_focus_block" | "file_changed" | ...

payload는 optional.

---

## 4.4 Done Definition
- [ ] 이벤트 1개를 넣으면 DB에 1행이 저장된다
- [ ] 서비스 재시작해도 DB가 유지된다
- [ ] 실패 케이스(잘못된 JSON 등)에서 서비스가 죽지 않는다

---

## 4.5 다음 단계로 넘어가기 전 팁
- 지금 단계에서는 “프라이버시/우선순위”를 **아직** 깊게 넣지 않아도 된다.
- 다만 다음 단계(4단계)에서 바로 붙일 예정이니, 이벤트 구조는 가능한 빨리 `EventEnvelope` 중심으로 잡아두는 게 좋다.
