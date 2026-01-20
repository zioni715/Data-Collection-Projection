# 10. Routine Candidate Builder
**목표:** 자동화/추천을 위한 “반복 루틴 후보”를 구조화해서 만든다.  
(추천 문장 생성은 Super Agent에서, 수집 프로그램은 후보만 제공)

---

## 10.1 산출물
- routine_candidates 테이블(또는 파일)
- TOP N 루틴 후보 리스트 + 점수/근거

---

## 10.2 입력 데이터
- 세션 요약(session_summary)
- 특히 key_events 시퀀스 + 시간대/요일 정보

---

## 10.3 MVP 루틴 탐지 로직(가벼운 방식)
1) 세션별 key_events를 시간순으로 정리
2) n-gram(길이 3~6) 빈도 카운트
3) 주기성 점수 추가
   - 요일 반복(월요일 오전 등)
   - 월말/주말 같은 패턴
4) TOP 5~10 후보 선택

---

## 10.4 루틴 후보 스펙(권장 필드)
- routine_id
- pattern: ["refresh_pivot", "export_pdf", "send_clicked"]
- supports: 최근 N일 반복 횟수
- last_seen
- time_pattern: weekday, time_range
- confidence: 0~1 스코어(단순 가중치 합이라도 OK)
- evidence_session_ids: 근거 세션 id 목록

---

## 10.5 검증 기준
- [ ] 반복 작업이 실제로 TOP 후보에 올라온다(테스트 데이터라도)
- [ ] 후보 개수/크기가 과하지 않다
- [ ] 민감 내용 없이도 의미가 전달된다(이벤트 시퀀스 중심)

---

## 10.6 다음 단계
세션 요약 + 루틴 후보 + 최근 컨텍스트를 묶어 **handoff package** 생성(9단계).
