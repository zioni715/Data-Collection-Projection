# 8_Testing_and_Replay.md
이 단계는 “수집 프로그램이 안정적으로 동작한다”를 보장하기 위한 **테스트/리플레이(재현) 체계**를 만드는 단계입니다.  
OS 센서, Add-in 이벤트는 환경 의존이 크기 때문에 **샘플 이벤트 주입/리플레이**가 있으면 개발 속도가 확 올라갑니다.

---

## 목표
- 이벤트 스트림을 **파일/HTTP로 주입**해서 파이프라인을 반복 테스트
- 회귀 테스트: 세션화/루틴 후보가 변경되어도 품질이 망가지지 않게 체크
- 버그 재현: 현장에서 나온 문제를 “이벤트 로그”만으로 재현

---

## 해야 할 일(체크리스트)

### 1) 샘플 이벤트 세트 만들기
- OS 중심 샘플: app focus block, idle, file_changed
- Add-in 샘플: excel.export_pdf, outlook.send_clicked 등
- 개인정보 없는 더미 데이터로 구성

**산출물**
- `tests/fixtures/sample_events_day1.jsonl`
- `tests/fixtures/sample_events_weekly.jsonl`

### 2) 이벤트 리플레이 도구(간단한 CLI) 만들기
기능:
- jsonl을 읽어서 시간 간격을 유지하거나(옵션), 고속으로(옵션) ingest endpoint로 전송
- 실패/드롭 통계 출력

**산출물**
- `scripts/replay_events.py` (또는 `scripts/replay_events.sh`)
- 문서: `Process/12_Testing_and_Replay.md`의 실행 방법 섹션(간단히)

### 3) 파이프라인 단위 테스트
최소 단위 테스트 추천:
- privacy: 마스킹/해시가 적용되는지
- priority: P0/P1/P2 분류가 맞는지
- sessionizer: idle/종결 이벤트로 세션이 기대대로 끊기는지
- routine: n-gram이 예상대로 TOP에 나오는지

**산출물**
- `tests/test_privacy.py`
- `tests/test_priority.py`
- `tests/test_sessionizer.py`
- `tests/test_routine.py`

### 4) 품질 기준(Assertion) 정의
예시:
- 하루 샘플에서 세션 개수 3~20개 범위
- routine 후보 상위 3개가 기대 패턴과 일치
- handoff payload 크기 제한(예: < 50KB)

**산출물**
- `tests/test_handoff_size.py` (선택)

---

## 완료 기준
- [ ] 샘플 이벤트만으로도 end-to-end(저장→세션→루틴→handoff) 테스트가 된다
- [ ] 현장에서 발생한 버그를 “이벤트 로그 리플레이”로 재현할 수 있다
- [ ] 주요 로직(privacy/session/routine)의 회귀 테스트가 준비되어 있다
