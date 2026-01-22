# First Logging Report (초기 실수집 리포트)

## 1) 스냅샷 요약
- 수집 기간(KST): `2026-01-21 09:00:00` ~ `2026-01-22 10:02:12` (약 25.04시간)
- 총 이벤트 수: 761 (약 30.4 events/hour)
- DB 파일 크기: `collector.db` 0.75 MB (786,432 bytes)
- 로그 파일 크기: `logs/collector.log` 0.42 MB (444,052 bytes)
- WAL/SHM 파일: 없음 (정상 종료 후 체크포인트 완료 상태)

## 2) 무결성/안전성 점검
- SQLite integrity_check: **ok**
- ERROR 로그: 0건
- retention 로그: 삭제 0건, vacuum 실행됨(정상)

## 3) 수집량/분포 요약
### 3-1. 이벤트 타입 Top
- os.app_focus_block: 420
- os.idle_start: 110
- os.idle_end: 110
- os.file_changed: 102
- excel.export_pdf: 5
- outlook.send_clicked: 5
- excel.refresh_pivot: 3
- outlook.attachment_added_meta: 3
- outlook.compose_started: 3

### 3-2. 우선순위 분포
- P1: 747
- P0: 13
- P2: 1

### 3-3. 소스 분포
- os: 742
- outlook_addin: 11
- excel_addin: 8

### 3-4. 센서 품질 신호
- idle_start vs idle_end: 110 vs 110 (정상 페어)
- file_changed: 102 (파일 감시 이벤트 정상 수집)
- focus_block: 420 (주요 앱 사용 블록 생성됨)

## 4) 세션/루틴/핸드오프 결과
- sessions: 31
- routine_candidates: 3
- handoff_queue: 1

## 5) 프라이버시 사후 감사(요약)
- redaction 적용 이벤트: 761 / 761 (100%)
- redaction 태그 총합: 1,610

잠재 민감 문자열 탐지(간단 스캔):
- payload_json 내 `@` 포함: 24
- raw_json 내 `@` 포함: 30
- payload_json 내 경로 패턴(`C:\`, `/Users/`, `/home/`): 197
- raw_json 내 경로 패턴: 200

주의/해석:
- `raw_json`은 원문 이벤트가 남을 수 있음 (보안 정책상 필요 없으면 저장 비활성화 추천).
- payload에서도 일부 패턴이 남아있으므로, 수집 키(`path`, `file_path` 등)와 마스킹 규칙 재점검 권장.

## 6) 로그 관측 요약(collector.log 기준)
- 로그 라인 수: 1,352
- metrics_minute 로그: 603회
- ERROR: 0건
- 최근 metrics_minute 샘플:
  - ingest.received_total: 307
  - ingest.ok_total: 307
  - store.insert_ok_total: 207
  - pipeline.dropped_total: 89
  - drop.reason.allowlist: 89
  - queue.depth: 0

메모:
- counters는 **프로세스 실행 단위**로 누적됨(재시작 시 초기화).
- 로그에는 과거 실행(run_id가 다른) 기록이 섞여 있을 수 있음.

## 7) 리소스 사용량(실측)
측정 당시 코어 실행 상태에서 아래 값을 확인:
- 프로세스: python (PID 35740)
- 시작 시간: 2026-01-22 오전 10:12:02
- CPU: 0.3125 (누적 CPU 시간, seconds)
- 메모리: WorkingSet 32,944,128 bytes (약 31.43 MB)
- 커맨드라인:
  - `"C:\Users\SAMSUNG\anaconda3\envs\DATA_C\python.exe" -m collector.main --config configs\config.yaml`

측정 방법(참고):
```powershell
# collector.main 프로세스 찾기
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*collector.main*' } |
  Select-Object ProcessId, CommandLine, WorkingSetSize

# 프로세스 ID로 상세 확인
Get-Process -Id <PID> | Select-Object CPU, WorkingSet64, StartTime
```

## 8) 첫 수집 기준 결론
- 수집/저장 파이프라인 정상 동작 확인 (insert_ok 증가, ERROR 없음).
- 센서 이벤트(Idle, Focus block, File watcher)가 균형 있게 수집됨.
- allowlist drop 발생(89건) → 필요 앱 확장 or 요약 정책 검토 필요.
- privacy 적용은 전량 수행됐으나, raw_json 및 일부 payload에 민감 패턴 잔존 가능성.

## 9) 다음 실험 권장 체크리스트
1. raw_json 저장 필요 여부 결정(필요 없으면 저장 비활성화).
2. allowlist/denylist 재정의(업무 앱 확대).
3. file_watcher 경로/확장자 필터 조정(노이즈 감소).
4. 리소스 사용량(평균 CPU/메모리) 측정 기록.
5. 하루 단위 요약 리포트 자동화 필요 여부 판단.

## 10) 1차 실수집 리뷰 및 2차 개발 우선순위
### 10-1. 잘 된 점
- 안정성/무결성: 25시간 수집에서 integrity_check=ok, ERROR 0건, 정상 종료 체크포인트 확인.
- 센서 품질: idle_start/end 페어링 정상, focus_block이 메인 이벤트로 안정 수집.
- P0 이벤트 유입: export/send 계열이 실제로 들어와 세션/루틴 품질 향상 여지 확보.
- 리소스 사용량: 메모리 약 31MB로 장시간 상주에 유리.

### 10-2. 우선 이슈 2개
이슈 A) 프라이버시 패턴 잔존
- raw_json/payload에서 `@`, 경로 패턴이 여전히 탐지됨.
- 대응 권장:
  1. raw_json 저장 OFF(또는 암호화/초단기 retention)
  2. privacy_rules에서 path/url/email 키는 강제 해시/드롭
  3. 패턴 스캔을 테스트/CI로 자동화

이슈 B) allowlist drop 정책
- allowlist 외 앱 이벤트가 드롭되는 흐름이 존재.
- 사용자 친화 로그를 위해서는 다음 중 하나로 방향 결정:
  1. 업무 앱 allowlist 확대(앱명+사용시간만 수집)
  2. denylist 유지하되 “차단 앱 사용시간”만 요약으로 기록

### 10-3. 세션/루틴/핸드오프 해석
- sessions 31 / routine_candidates 3 / handoff_queue 1 → 동작은 확인됨.
- 세션 분포(평균/중앙값/최장)를 추가로 확인하면 튜닝 방향이 명확해짐.
- 루틴 후보가 적다면 n-gram 길이를 2~3으로 낮추거나 의미 P1 이벤트 포함 범위를 조정.

### 10-4. 2차 개발 로드맵(추천)
P0 (당장)
1. raw_json 저장 OFF + privacy_rules 강화(경로/이메일/URL)
2. HTTP access log를 INFO에서 분리 또는 레벨 하향

P1 (이번 주)
3. 사용자 친화 Activity Feed 로그(블록/분 요약)
4. allowlist/denylist 정책 재정의

P2 (다음)
5. 1일 요약 리포트 자동 생성(세션/앱 시간/P0 이벤트)

### 10-5. 추가 체크(2차 전 1회)
1. 세션 평균/중앙값/최장 길이
2. file_changed 상위 폴더/확장자 분포
3. P0 이벤트가 있는 세션의 전후 앱 흐름
4. drop이 allowlist 외 debounce/queue_full로도 발생하는지
5. DB에 원문 경로/이메일이 실제로 남아있는지 샘플 확인

## 11) allowlist 사용자 맞춤 자동화 방안
가능하지만 “완전 자동”은 프라이버시 리스크가 커서,
실전에서는 **자동 수집 → 후보 추천 → 사용자 승인** 형태가 가장 안전함.

### 11-1. 실사용 기반 자동 후보 생성(권장)
이미 수집 중인 `os.app_focus_block`을 이용해서
**지난 1~3일간 실제로 많이 사용한 앱 TOP N**을 후보로 만든다.

추천 기준 예시:
- 하루 누적 사용 **10분 이상**
- 또는 세션 기준 **3회 이상** 등장

장점:
- 설치 앱 전체를 크롤링할 필요 없음
- 실제로 쓰는 앱만 후보에 올라옴

### 11-2. allowlist 정책을 2단계로 분리
사용자마다 요구가 다르므로, “수집 강도”를 분리하면 깔끔하다.

A) FULL 허용(업무 앱)
- EXCEL / OUTLOOK / VSCode 등
- 앱명 + 사용시간 + 이벤트 유형은 허용
- 본문/내용/파일 경로는 기존 프라이버시 규칙대로 제거

B) META-ONLY 허용(개인/민감 앱)
- 메신저/브라우저 계열
- **앱명 + 사용시간 + 빈도만 저장**
- 창 제목/리소스/파일 경로는 모두 드롭

### 11-3. 자동 크롤링을 쓴다면 가능한 수단
1) 실행 중 프로세스/윈도우 목록 기반
- 포그라운드 앱을 주기적으로 수집
- `process_name → 앱명` 매핑으로 후보 생성

2) 설치된 앱 목록 기반(Windows 레지스트리/Start Menu)
- 설치 목록은 참고용, 최종 결정은 실사용 기준이 안전

### 11-4. 운영 흐름(권장)
1) Warm-up 1~3일
- allowlist 밖 앱도 완전 드롭하지 않고 META-ONLY로 집계
2) 자동 추천 생성
- TOP 사용 앱을 FULL / META-ONLY / DENY로 분류 제안
3) 사용자 승인(1회)
- 이후 정책 고정 또는 주기적 재추천

### 11-5. 최소 변경 구현 아이디어
현재 allowlist 미스는 드롭으로 끝남.
이를 **META-ONLY 다운그레이드**로 바꾸면 체감이 크게 좋아짐.

예시 변경:
- allowlist 실패 시 `event_type=activity_meta`로 전환
- payload 제거, `app + duration_sec`만 저장
- 별도 집계 테이블 `app_usage_daily(app, date, focus_sec, blocks, last_seen_ts, mode)`
