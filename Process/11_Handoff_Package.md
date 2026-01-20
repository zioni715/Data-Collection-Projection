# 11. Handoff Package and Queue
**목표:** Local Super Agent가 바로 사용할 수 있는 **경량 패키지**를 만들어 큐에 적재한다.  
(여기서부터 n8n은 다루지 않음)

---

## 11.1 산출물
- handoff.schema.json(권장)
- handoff_queue 테이블 적재 로직
- 최신 handoff payload 생성 주기(예: 1~5분 또는 이벤트 기반)

---

## 11.2 handoff payload 구성(권장)
### 1) recent_context (최근 1~2분)
- active_app
- active_window_masked
- last_focus_blocks(요약 형태)
- last_key_events

### 2) recent_sessions (최근 1~3개)
- session_summary 그대로 또는 축약본

### 3) routine_candidates (TOP 5~10)
- routine 후보 스펙 그대로

### 4) privacy_state
- content_collection=false
- denylisted_apps_active 여부
- redaction rules version(optional)

---

## 11.3 큐 프로토콜(권장)
- status: pending → consumed
- Super Agent가 읽고 consumed로 바꾸는 방식(다음 단계)

---

## 11.4 검증 기준
- [ ] payload가 수 KB~수십 KB 내로 유지된다
- [ ] 원문 경로/메일 주소/본문이 포함되지 않는다
- [ ] 큐에 pending이 쌓이고, 중복/폭주 없이 최신 상태가 유지된다

---

## 11.5 다음 단계
운영을 위해 retention/cleanup과 관측(로그/메트릭)을 붙인다(10단계).
