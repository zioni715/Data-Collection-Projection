# 9. Sessionization and Session Summary
**목표:** raw events(원장)를 **세션(Session)** 으로 묶어 “업무 단위”를 만든다.  
세션 요약은 Super Agent에게 넘길 핵심 입력이 된다.

---

## 9.1 산출물
- sessions 테이블(또는 파일 캐시)
- 세션 생성 규칙(Idle/종결 이벤트 기반)
- session_summary JSON 생성

---

## 9.2 세션 분할 규칙(MVP)
### 기본 종료 조건
- idle >= 10~15분 → 세션 종료

### 종결 이벤트(가중치)
- send_clicked(Outlook)
- export_pdf/export_csv(Excel)
- file_saved(중요 산출)

→ 이런 이벤트가 나오면 “업무가 끝났다” 가능성이 높아 세션 경계로 활용.

### 유지 조건
- 앱 전환이 있어도 “짧은 시간 내” 이어지면 같은 세션
  - 예: Excel → Outlook (5분 이내)

---

## 9.3 세션 요약에 포함할 필드(권장)
- session_id
- start_ts / end_ts / duration_sec
- apps_timeline: ["EXCEL(18m)", "OUTLOOK(6m)"]
- key_events: ["refresh_pivot", "export_pdf", "send_clicked"]
- resources: file/email/web hash 목록
- confidence(간단 스코어라도 OK)

---

## 9.4 검증 기준
- [ ] 하루 이벤트를 세션으로 묶었을 때 세션 수가 현실적(예: 3~20개 수준)
- [ ] send_clicked가 세션 종료에 실제로 도움이 된다
- [ ] 세션 요약 크기가 과도하지 않다(세션당 수 KB 내)

---

## 9.5 다음 단계
세션이 생기면, 반복되는 세션/시퀀스를 찾아 **루틴 후보**를 만든다(8단계).
