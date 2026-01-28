# Third_Logging.md

## 1) 개요
3차 수집은 “초개인화에 필요한 활동 디테일 확보”를 목표로 진행했다.
주요 강화 포인트는 **디테일 허용 앱 확대(Chrome/Whale/Notion/Discord/VSCode/KakaoTalk)**,
**브라우저 확장 기반 URL 수집**, **실시간 디테일 로그(JSON + 텍스트) 분리**다.

## 2) 수집 기간 (KST 기준)
- 시작: 2026-01-24 06:11:43
- 종료: 2026-01-27 09:25:41
- 총 수집 시간: 약 75.2시간

## 3) 수집 구성 (run3)
- Core: `configs/config_run3.yaml`
- DB: `collector_run3.db`
- 로그:
  - `logs/run3/collector.log` (JSON)
  - `logs/run3/activity_detail.log` (디테일 JSON)
  - `logs/run3/activity_detail.txt` (디테일 텍스트 요약)
- 브라우저 상세 수집: `browser_extension/` 확장
- 프라이버시 룰: `configs/privacy_rules_run3.yaml` (full URL 허용)

## 4) 실행 방법 (요약)
```powershell
$env:PYTHONPATH="src"
python -m collector.main --config configs\config_run3.yaml
```

센서 (예):
```powershell
$env:PYTHONPATH="src"
python -m sensors.os.windows_foreground --ingest-url "http://127.0.0.1:8080/events" --poll 1
```

브라우저/디테일 로그:
```powershell
Get-Content .\logs\run3\activity_detail.log -Tail 50 -Wait
Get-Content .\logs\run3\activity_detail.txt -Tail 50 -Wait
```

## 5) 데이터 요약
### 5-1. 총 이벤트
- events 총합: **866**
- event_type 상위:
  - `os.app_focus_block`: 609
  - `browser.tab_active`: 199
  - `os.idle_start`: 29
  - `os.idle_end`: 29

### 5-2. source 분포
- `os`: 667
- `browser_extension`: 199

### 5-3. priority 분포
- P1: 866 (현재 수집 이벤트가 모두 P1 처리됨)

## 6) 디테일 수집 결과 (activity_details)
- activity_details 행 수: **73**
- 디테일 로그 샘플 수:
  - 총 `activity_detail` 로그: 360건
  - 앱별 로그 개수(상위):
    - CODE.EXE: 118
    - CHROME.EXE: 94
    - NOTION.EXE: 78
    - KAKAOTALK.EXE: 36
    - WHALE.EXE: 23
    - DISCORD.EXE: 11

### 6-1. 앱별 사용시간(상위)
- CODE.EXE: 12,582s (≈ 209.7m)
- NOTION.EXE: 6,845s (≈ 114.1m)
- CHROME.EXE: 2,702s (≈ 45.0m)
- KAKAOTALK.EXE: 2,123s (≈ 35.4m)
- WINDOWSTERMINAL.EXE: 1,699s (≈ 28.3m)
- WHALE.EXE: 1,537s (≈ 25.6m)
- DISCORD.EXE: 372s (≈ 6.2m)

> 디테일 허용 앱은 **페이지/채널/문서 제목(window_title)** 수준까지 기록되며,
> `title_label`로 반복 식별 가능하다. (원문 제목도 기록됨)

## 7) 브라우저 상세 수집
- 브라우저 확장 이벤트: `browser.tab_active` 199건
- URL + title 수집 가능 (full URL 허용 설정)

## 8) 로그/리소스 규모
- DB 크기: 약 **1.09 MB** (1,138,688 bytes)
- 로그 크기:
  - `collector.log`: 약 0.88 MB
  - `activity_detail.log`: 약 0.21 MB
  - `activity_detail.txt`: 약 0.08 MB

## 9) 드롭/프라이버시 관측
- 마지막 metrics snapshot 기준:
  - ingest.received_total: 696
  - ingest.ok_total: 696
  - privacy.redacted_total: 660
  - pipeline.dropped_total: 36
  - drop.reason.allowlist: 36
- queue.depth는 0으로 안정

## 10) 수집 품질 관찰 (의미 있는 변화)
- **브라우저 확장 수집**으로 “어떤 페이지/URL”을 구체적으로 파악 가능
- 디테일 허용 앱 확대(Discord/KakaoTalk/VSCode)로 “대화방/파일/작업 문맥”까지 수집
- `activity_detail.txt`를 통해 **실시간 사용자 친화 로그 확인 가능**

## 11) 다음 개선 아이디어
1. 브라우저 URL 저장 정책을 선택형으로 분리 (full vs domain)
2. Notion/VSCode 제목 정규화(꼬리 제거/길이 제한)로 가독성 개선
3. P0 이벤트(업무 완료 이벤트)를 추가해 세션/루틴 품질 강화
4. 업무 앱 기본 allowlist(Office/Teams 등) 강화로 일반 사용자 패턴 대응

---

### 요약
3차 수집은 “디테일 기반 초개인화” 방향으로 한 단계 진척되었다. 특히 브라우저 확장과
디테일 로그 텍스트 출력이 결합되면서, **실시간으로 무엇이 수집되는지 확인 가능**해졌고,
활동 패턴 파악에 충분한 수준의 이벤트가 확보되었다.
