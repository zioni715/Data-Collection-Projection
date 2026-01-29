# Fourth Logging Report (Run4)

## 1) 수집 개요
- 수집 목적: 브라우저/업무앱 기반 활동 로그를 상세화하고, 요약/패턴/LLM 입력까지 자동 생성되는 파이프라인 검증
- 코어 실행: `python -m collector.main --config configs\config_run4.yaml`
- 센서 자동 시작: `sensors.auto_start: true` (foreground/idle/file_watcher)
- 브라우저 확장: Chrome/Whale 탭 활성 이벤트 + content_summary/content 전송
- 암호화: raw_json 암호화 ON (Fernet, key_path 사용)
- 수집 기간(UTC 기준): 2026-01-27T00:54:27Z ~ 2026-01-29T01:28:26Z  
  - 총 48시간 33분 59초
  - KST 기준: 2026-01-27 09:54:27 ~ 2026-01-29 10:28:26

## 2) DB 저장 결과 요약
**events 총 건수:** 1,875  
**event_type 분포 (상위):**
- os.app_focus_block: 1,055
- browser.tab_active: 546
- os.idle_start: 137
- os.idle_end: 137

**app 분포 (상위):**
- CHROME.EXE: 770
- CODE.EXE: 301
- OS: 274
- KAKAOTALK.EXE: 237
- WHALE.EXE: 103
- NOTION.EXE: 94
- WINDOWSTERMINAL.EXE: 53
- DISCORD.EXE: 40

**priority 분포:**
- P1: 1,875 (focus block 기반)
- P0/P2: 0 (이번 run4는 P1 중심 수집)

**activity_details 집계:**
- 총 rows: 149
- 앱별 힌트 개수(상위): Chrome 65 / Whale 42 / VSCode 21 / Discord 8 / Notion 6

**세션/루틴/핸드오프:**
- sessions: 0
- routine_candidates: 0
- handoff_queue: 0

## 3) 로그 파일 크기 (run4)
- `logs/run4/collector.log`: 2,113,370 bytes
- `logs/run4/activity_detail.log`: 521,115 bytes
- `logs/run4/activity_detail.txt`: 354,172 bytes

## 4) 요약/패턴/LLM 입력 파일
- daily summary: `logs/run4/daily_summary_2026-01-28.json` (2,231 bytes)
- pattern summary: `logs/run4/pattern_summary.json` (945 bytes)
- llm input: `logs/run4/llm_input.json` (1,838 bytes)

## 4-1) 로그 줄 수 및 경량화 지표
**로그 라인 수**
- `collector.log`: 7,499 lines
- `activity_detail.log`: 1,256 lines
- `activity_detail.txt`: 2,012 lines

**LLM 입력 라인 수**
- `llm_input.json`: 88 lines  
  (JSON 구조지만 line 기준 비교를 위해 줄 수로 환산)

**경량화 정도(파일 크기 기준)**
- `collector.log` → `llm_input.json`  
  - 2,113,370 bytes → 1,838 bytes  
  - 약 **0.087%** 크기 (≈ 1/1,150 수준)

**해석**
- 원장/로그는 수천 줄 단위이지만 LLM 입력은 수십 줄 수준으로 축소됨
- 패턴/요약을 통해 **LLM 입력이 크게 압축됨**을 확인

## 4-2) 로그 경량화 방식 (상세)
이번 run4의 경량화는 **“원장 → 요약 → 패턴 → LLM 입력”**의 다단계 축소 구조로 구성됨.

1) **원장(events)**  
   - 모든 이벤트를 저장하되, payload는 프라이버시 규칙으로 정리  
   - `content` 같은 고용량 본문은 payload에서 제거  
   - 원문(full content)은 암호화된 raw_json에만 보관

2) **일일 요약(daily_summary)**  
   - 앱별 사용시간 합산  
   - 상위 타이틀 힌트(top_titles) 제한  
   - 핵심 이벤트(P0/P1)만 유지

3) **패턴 요약(pattern_summary)**  
   - 요일/시간대 패턴만 남김  
   - 반복 시퀀스(n-gram) 후보만 추출  
   - 세부 이벤트는 제거

4) **LLM 입력(llm_input)**  
   - max-bytes 제한을 걸어 사이즈 초과 시 자동 축소  
   - 축소 순서: `top_titles` → `top_apps` → `hourly_patterns` → `key_events`  
   - 결과적으로 수천 줄 로그가 수십 줄 입력으로 축소

**결과적으로:**  
- “정밀 원본”은 암호화 raw_json에 유지  
- “패턴/추천용 입력”은 수십 줄로 축소됨  
→ 초개인화는 유지하면서도 LLM 입력 크기를 안전 범위로 줄임

## 5) 이번 run4에서 추가/강화된 점
1) 센서 자동 시작
   - 코어 실행 시 foreground/idle/file_watcher 자동 실행
2) 브라우저 상세 수집
   - 탭 활성 이벤트 + content_summary/content 전송
3) 원문(raw_json) 암호화 저장
   - key_path(`secrets/collector_key.txt`)로 자동 로드
4) activity_detail 집계 유지
   - 앱 + title_hint 기준 사용 시간 누적

## 6) 프라이버시/보안 체크
- payload에는 `content` 제거 (drop_payload_keys 적용)
- `content_summary`는 마스킹/길이 제한 적용
- full content는 암호화된 `raw_json`에만 저장

## 6-1) 콘텐츠 수집 품질 (브라우저 확장)
- browser.tab_active 이벤트: 546건
- raw_json 복호화 샘플 기준, **content_summary가 포함된 이벤트는 0건**
  - 원인 가능성: 확장 재로드 누락, content script 미주입, 페이지 권한/도메인 제한
  - 조치: 브라우저 확장 Reload 후 재수집 권장

## 7) 문제/관찰 사항
- P0 이벤트가 없어 세션/루틴 생성이 진행되지 않음
  → 업무 완료 이벤트(P0) 발생이 없으면 세션/루틴 품질이 낮아짐
- 활동 로그는 충분히 쌓였으나, 패턴/루틴 추출에 필요한 “완료 이벤트”가 부족

## 7-1) 루틴 파악 결과
**이번 run4에서는 루틴 후보가 생성되지 않음**  
- `routine_candidates: 0` (DB 기준)
- 이유: P0 이벤트(완료/결정 이벤트)가 없어서 세션 경계 및 반복 시퀀스가 약함

**루틴 파악이 동작하는 방식(정상 흐름):**
1) `sessions` 생성  
   - `os.idle_start`, `gap`, `P0 이벤트` 기준으로 세션 분리
2) `key_events` 추출  
   - 세션 요약에서 의미 있는 이벤트(P0/P1)를 뽑음
3) **n-gram 시퀀스 카운트**  
   - 예: `["excel.export_pdf","outlook.send_clicked"]`
4) `routine_candidates` 저장  
   - 반복 횟수(support) + confidence 계산

**루틴을 실제로 생성하려면**
- P0 이벤트 입력(예: `excel.export_pdf`, `outlook.send_clicked`)이 반드시 필요  
- 세션을 생성한 뒤 `build_routines.py` 실행 시 후보가 나옴

## 8) 다음 개선 방향
1) P0 이벤트 추가 테스트
   - `excel.export_pdf`, `outlook.send_clicked` 등 실제 입력 또는 리플레이
2) 세션 빌더 실행 후 `sessions` 생성 확인
3) 브라우저 콘텐츠 capture 도메인 제한 적용
   - `DOMAIN_ALLOWLIST`로 민감 사이트 제외
4) 디테일 로그에 “활동 요약 텍스트” 강화
   - `activity_detail.txt` 기반 일일 리포트 자동화

## 9) 실행/재현 체크리스트
1) 코어 실행
```powershell
$env:PYTHONPATH = "src"
python -m collector.main --config configs\config_run4.yaml
```
2) 브라우저 확장 reload
3) activity_detail 로그 확인
```powershell
Get-Content .\logs\run4\activity_detail.txt -Tail 30 -Wait
```
4) 요약 생성 재확인
```powershell
python scripts\build_daily_summary.py --config configs\config_run4.yaml --store-db
python scripts\build_pattern_summary.py --summaries-dir logs\run4 --since-days 7 --config configs\config_run4.yaml --store-db
python scripts\build_llm_input.py --config configs\config_run4.yaml --daily logs\run4\daily_summary_YYYY-MM-DD.json --pattern logs\run4\pattern_summary.json --output logs\run4\llm_input.json --store-db
```

## 10) 5차 수집(Next Run) 준비 리스트
1) 브라우저 확장 재로드 + content script 주입 확인  
   - content_summary가 실제로 들어오는지 확인
2) P0 이벤트 강제 테스트  
   - `excel.export_pdf`, `outlook.send_clicked` 리플레이로 세션/루틴 생성 확인
3) `sessions`/`routine_candidates` 자동 생성 확인  
   - `build_sessions.py`, `build_routines.py` 실행 후 row 확인
4) `DOMAIN_ALLOWLIST` 적용  
   - 민감 사이트 제외(로그 품질+프라이버시 확보)
5) 암호화 키 파일 백업  
   - `secrets/collector_key.txt` 안전 보관
6) activity_detail 품질 점검  
   - title_hint 중복/노이즈 정리 규칙 강화
