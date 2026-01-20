# 13_Service_and_Crash_Safety.md
이 단계는 수집 프로그램을 “개발용 스크립트”가 아니라 **상시 실행되는 로컬 에이전트**로 만들기 위한 운영 안정화 단계입니다.

---

## 목표
- 앱이 꺼지거나 재부팅돼도 **자동 재시작/복구**
- 이벤트 폭주/DB 잠금/네트워크 문제에도 **데이터 유실 최소화**
- 크래시 시 원인 추적(로그/덤프) 가능

---

## 해야 할 일(체크리스트)

### 1) 실행 형태 결정
- 개발: `python -m collector.main`
- 운영: Windows Service / macOS LaunchAgent / Linux systemd 중 택1(플랫폼별)

**산출물**
- `scripts/install_service.ps1` (윈도우면 추천)
- `scripts/uninstall_service.ps1`
- 문서: 설치/삭제/업데이트 방법

### 2) Backpressure & Spooling
이벤트가 순간적으로 많아질 때:
- in-memory queue가 꽉 차면 P2부터 드롭 또는
- 디스크 스풀 파일(jsonl)로 임시 저장 후 배치 처리

**산출물**
- 설계 문서 + 구현(선택): `collector/spool.py`

### 3) SQLite 안정성 설정
- WAL 모드
- 배치 insert(트랜잭션)
- DB 잠금 발생 시 재시도/백오프

**산출물**
- store 레벨 retry 정책 문서화

### 4) 크래시/재시작 시 복구
- 마지막 처리 위치(cursor) 또는 마지막 ts 기반 재처리 정책
- handoff_queue 중 pending 처리 유지

**산출물**
- `collector/recovery.md` (간단 정책 문서라도)

### 5) 리소스 상한 설정
- CPU/메모리/디스크 상한
- 이벤트 처리량 제한(최대 eps)

---

## 완료 기준
- [ ] 재부팅 후 자동 실행된다
- [ ] 이벤트 폭주 상황에서 시스템이 다운되지 않는다(P2 드롭/스풀로 완충)
- [ ] 크래시가 나도 DB가 손상되지 않고 재시작 후 계속 수집된다
