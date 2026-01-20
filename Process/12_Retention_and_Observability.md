# 12. Retention and Observability
**목표:** 장시간 돌려도 리소스/안정성 문제가 없도록 “보관정책 + 관측”을 넣는다.

---

## 12.1 산출물
- retention job(주기 실행)
- 기본 로깅 + 에러 로깅
- 처리량/큐 적체 간단 메트릭(로그로라도)

---

## 12.2 보관 정책(권장 기본)
- raw events: 7~14일
- sessions summary: 60~90일
- routine candidates: 사용자 확정/중요 후보만 장기 보관(옵션)

---

## 12.3 cleanup 전략
- DB에서 ts 기준으로 삭제
- 인덱스 유지(삭제 후 vacuum은 상황에 따라)
- handoff_queue는 consumed 항목을 일정 기간 후 삭제

---

## 12.4 관측(운영 품질)
### 로깅
- ingest 파싱 실패
- privacy/masking 적용 로그(카운트)
- DB insert 실패
- sessionizer/routine builder 예외

### 메트릭(최소)
- events/sec
- queue depth
- dropped events count(P2)
- handoff 생성 주기/성공 여부

---

## 12.5 검증 기준
- [ ] 하루 이상 돌려도 DB 용량이 통제된다
- [ ] 에러가 발생해도 서비스가 죽지 않는다(재시작 가능)
- [ ] 문제 발생 시 “어디서 막혔는지” 로그로 추적 가능하다
