# Second Logging Report (2차 수집 리포트)

## 1) 스냅샷 요약
- 수집 기간(KST): `2026-01-22 11:09:18` ~ `2026-01-23 10:28:40` (약 23.32시간)
- 총 이벤트 수: 515 (약 22.1 events/hour)
- DB 파일 크기: `collector_run2.db` 0.63 MB (663,552 bytes)
- 로그 파일 크기: `logs/run2/collector.log` 0.63 MB (657,973 bytes)
- 사용 설정 파일: `configs/config_run2.yaml`
- 실행 센서: `windows_foreground` 중심 (focus block 생성)

## 2) First_Logging 대비 개선/변경점
- **DB/로그 분리 운영**: `collector_run2.db`, `logs/run2/collector.log`로 분리되어 1차와 비교가 쉬워짐.
- **사용자 친화 로그 활성화**: `activity_block`, `activity_minute` 로그가 생성되어 “무엇을 했는지” 확인 가능.
- **수집 범위 축소**: 이번 수집은 `os.app_focus_block`만 생성(Idle/File/Add-in 이벤트는 없음).
- **allowlist 자동 추천 시도**: 추천 기준 적용했으나 추가 후보 0건 → 기존 allowlist 유지.

## 3) 이벤트 분포 요약
### 3-1. 이벤트 타입 분포
- os.app_focus_block: 515

### 3-2. 우선순위 분포
- P1: 515

### 3-3. 소스 분포
- os: 515

### 3-4. Focus block 품질 지표
- 평균 duration: 162.8s
- 중앙값 duration: 12s
- 최소/최대: 2s / 46,678s  
  (장시간 동일 앱 유지 시 큰 블록이 발생)

## 4) 앱 사용 시간 TOP (focus block 합산)
- WINDOWSTERMINAL.EXE: 951.6m
- CODE.EXE: 135.0m
- NOTION.EXE: 89.8m
- CHROME.EXE: 78.7m
- WHALE.EXE: 67.3m
- KAKAOTALK.EXE: 64.0m
- DISCORD.EXE: 11.0m
- MSEDGE.EXE: 0.1m

## 5) 프라이버시/민감 패턴 점검(간단 스캔)
- redaction 적용 이벤트: 515 / 515 (100%)
- redaction 총합: 1,545
- payload_json 내 `@` 포함: 7
- raw_json 내 `@` 포함: 7
- payload/raw 내 경로 패턴(`C:\`, `/Users/`, `/home/`): 0

메모:
- 이번 수집은 focus block만 포함되어 경로 패턴 잔존은 없음.
- `@` 포함은 창 제목/앱 UI 텍스트 영향 가능성 → 필요 시 마스킹 규칙 강화 검토.

## 6) 로그 분석(collector.log)
- 총 로그 라인: 1,985
- JSON 파싱 오류: 0
- 레벨 분포: INFO 1,985 (ERROR 0)
- 주요 이벤트 카운트:
  - metrics_minute: 789
  - activity_block: 361
  - activity_minute: 149
  - POST /events 200: 668
  - retention: 14

최근 metrics_minute 요약(로그 기준):
- ingest.received_total: 664
- ingest.ok_total: 664
- store.insert_ok_total: 512
- pipeline.dropped_total: 74
- drop.reason.allowlist: 74
- queue.depth: 0

주의:
- 로그 카운터는 “프로세스 기준 누적”이라 재시작/flush 타이밍과 차이가 날 수 있음.
- **DB count(515)가 최종 기준**으로 보는 것이 안전함.

## 7) 리소스 사용량
이번 2차 수집에서는 별도 CPU/메모리 스냅샷을 기록하지 못했음.  
다음 수집 때 아래 방식으로 기록 권장:

```powershell
# collector.main 프로세스 찾기
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*collector.main*' } |
  Select-Object ProcessId, CommandLine, WorkingSetSize

# 상세 확인
Get-Process -Id <PID> | Select-Object CPU, WorkingSet64, StartTime
```

## 8) 2차 수집 구동 방식(재현용)
```powershell
# Core 실행 (run2 설정)
cd C:\Data-Collection-Projection
conda activate DATA_C
$env:PYTHONPATH = "src"
python -m collector.main --config configs\config_run2.yaml

# 로그 확인
Get-Content .\logs\run2\collector.log -Tail 50 -Wait

# 센서 (foreground만)
python -m sensors.os.windows_foreground --ingest-url "http://127.0.0.1:8080/events" --poll 1
```

## 9) 요약 결론
- 2차 수집은 **분리된 DB/로그 환경에서 안정적으로 동작**했고, 사용자 친화 로그도 정상 출력됨.
- 이번 수집은 focus block 중심이라 **앱 사용 시간 요약에 최적화**되어 있음.
- allowlist drop이 여전히 존재하므로, 3차에서는 “메타 전용 허용(앱명+시간)” 정책 검토가 유용함.

## 10) 다음 수집 전 체크리스트(추천)
1. allowlist 추천 기준을 낮춰 후보 확인(필요 앱이 드롭되는지 확인)
2. access log 분리/레벨 조정(POST /events 로그가 많음)
3. 리소스 스냅샷 기록(시작/종료 시점 최소 1회)
4. idle/file watcher 추가 여부 결정(세션 품질 개선 목적)
