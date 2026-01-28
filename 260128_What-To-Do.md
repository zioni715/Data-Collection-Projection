# 260128 고도화 진행 내역 (What-To-Do)

## 1) 데이터셋 축소 파이프라인
- **daily_summary 생성**: 하루 단위 요약(앱 사용시간/핵심 이벤트/타이틀 힌트)
  - `scripts/build_daily_summary.py`
  - 출력: `logs/run4/daily_summary_YYYY-MM-DD.json`
- **pattern_summary 생성**: 최근 N일 패턴(요일/시간대/반복 시퀀스)
  - `scripts/build_pattern_summary.py`
  - 출력: `logs/run4/pattern_summary.json`
- **llm_input 생성**: LLM 입력용 경량 데이터셋
  - `scripts/build_llm_input.py`
  - 출력: `logs/run4/llm_input.json`

## 2) LLM 입력 크기 제한 + 자동 압축
- `build_llm_input.py`에 `--max-bytes` 지원
- 초과 시 자동 축소 로직 적용
  - `top_titles` 줄이기 → `top_apps` 축소 → `hourly_patterns` 축소 → `key_events` 축소

## 3) 추천 생성 (LLM 기반 + 한국어 문장 강화)
- 추천 JSON 스키마 고정: `schemas/recommendations.schema.json`
- LLM 프롬프트에 스키마/유효성 가이드 포함
- 추천 문장에 **시간/상황 문맥** 반영
  - 예: `09:00 (최근 3일 평균 45분 Chrome 사용)`
- 스크립트:
  - `scripts/generate_recommendations.py`
  - 출력: `activity_recommendations.md` / `activity_recommendations.json`

## 4) 자동화 트리거 확장
- 지원 액션:
  - `open_app`, `open_url`, `open_path`, `create_file`, `none`
- 실행 스크립트:
  - `scripts/execute_recommendations.py`
- **CLI 승인 모드** 추가:
  - `--approve prompt|yes|no`
- **메뉴 기반 다중 선택** 지원:
  - `--menu` + `--preview`

## 5) create_file 템플릿 자동 선택
- 앱별 템플릿 자동 매핑:
  - Notion → `templates/notion.md`
  - VSCode → `templates/vscode.md`
  - Chrome → `templates/chrome.md`
- 기본 템플릿:
  - `templates/default.md`, `templates/report.md`, `templates/meeting.md`, `templates/summary.md`

## 6) 코어 종료 시 자동 요약 + 추천 + 실행
- `post_collection` 파이프라인 확장
  - daily → pattern → llm_input → recommendations → (자동화 실행)
- 코어 종료 후 자동 실행됨

## 7) 추가/수정된 파일 목록
- 스크립트
  - `scripts/build_daily_summary.py`
  - `scripts/build_pattern_summary.py`
  - `scripts/build_llm_input.py`
  - `scripts/generate_recommendations.py`
  - `scripts/execute_recommendations.py`
  - `scripts/run_post_collection.ps1`
- 스키마
  - `schemas/recommendations.schema.json`
- 템플릿
  - `templates/default.md`
  - `templates/report.md`
  - `templates/meeting.md`
  - `templates/summary.md`
  - `templates/chrome.md`
  - `templates/notion.md`
  - `templates/vscode.md`

## 8) 바로 실행 가능한 체크리스트
1. **요약 생성**
   ```powershell
   python scripts/build_daily_summary.py --config configs/config_run4.yaml
   python scripts/build_pattern_summary.py --summaries-dir logs/run4 --since-days 7
   python scripts/build_llm_input.py --daily logs/run4/daily_summary_YYYY-MM-DD.json --pattern logs/run4/pattern_summary.json --output logs/run4/llm_input.json
   ```
2. **추천 생성**
   ```powershell
   python scripts/generate_recommendations.py --config configs/config_run4.yaml --input logs/run4/llm_input.json --output-md logs/run4/activity_recommendations.md --output-json logs/run4/activity_recommendations.json
   ```
3. **추천 실행(메뉴+미리보기)**
   ```powershell
   python scripts/execute_recommendations.py --input logs/run4/activity_recommendations.json --menu --preview --approve prompt
   ```

## 9) 다음 고도화 아이디어
- 추천 문장에 **상황 힌트(최근 top title)** 포함
- 템플릿 자동 매핑 고도화 (Discord/KakaoTalk 포함)
- CLI 메뉴에서 템플릿 미리보기 강화
- 추천 결과를 자동 실행 스케줄러와 연결

## 10) 추가 고도화(오늘 진행)
- 추천 문장 문맥 강화
  - 시간대/요일/패턴 기반 문맥 포함
- 시퀀스 패턴 기반 create_file 추천
- CLI 미리보기 옵션 강화
  - `--menu --preview --preview-template`

## 10-1) Chrome/Notion 상세 수집 확장
- 브라우저 확장에 **콘텐츠 요약/본문 추출** 추가
  - `browser_extension/content.js` 추가
  - `content_summary` + `content` 전송
- 개인정보 보호를 위해 **payload에서는 content 제거** 유지
  - full content는 `raw_json`에만 남도록 유지
- run3/run4 설정에서 **암호화 토글 추가**
  - 현재는 “복호화 번거로움” 때문에 **암호화 비활성 상태**
  - 필요 시 `encryption.enabled: true`로 재활성화

## 11) 회의 체크리스트
- [ ] 데이터 수집 지속 + Mock 데이터 기반 패턴 파악 시작
- [x] DB 로그 줄 수 축소 전략 확정
      (3일 7,500줄 → 2차 요약 → 3차 요약 or LLM 직접 입력)
- [ ] 하드코딩 시간 필터(9-6 or 24) vs 앱 기준 필터 선택

## 12) 패턴 고도화 진행
- Mock 패턴 데이터 생성 스크립트 추가
  - `scripts/generate_mock_events.py`
- 패턴 요약 확장
  - `weekday_patterns`, `sequence_patterns`, `confidence`
- LLM 입력 필터 추가
  - `scripts/build_llm_input.py`에 `--include-apps`, `--hours` 지원

## 13) 패턴 품질 평가
- `scripts/evaluate_pattern_quality.py`로 품질 지표 산출
- 커버리지/반복성/일관성 지표 확인
- JSON 리포트 출력

## 14) 요약 DB + 장기 유지 전략
- 요약 전용 DB 지원
  - `daily_summaries`, `pattern_summaries`, `llm_inputs` 테이블 추가
- `--store-db` 옵션으로 요약 DB 저장
- post_collection에서 요약 DB 자동 저장
- 요약 DB 전용 retention 스크립트 제공
  - `scripts/retention_summary_only.py`

## 15) 원본 보존(Cold Archive) + 장기 전략
- Raw 이벤트 아카이브
  - `scripts/archive_raw_events.py` → `archive/raw/raw_YYYY-MM-DD.jsonl.gz`
  - `--delete-after`로 DB 정리 가능
- 아카이브 재생
  - `scripts/replay_archive_events.py`
- 아카이브 무결성/월간 합치기
  - `scripts/archive_manifest.py`
  - `scripts/verify_archive_manifest.py`
  - `scripts/compact_archive_monthly.py`
- 스케줄러 등록
  - `scripts/install_archive_task.ps1`
  - `scripts/install_archive_monthly_task.ps1`

## 16) 센서 자동 시작 (코어 실행 시 동시 구동)
- `sensors.auto_start` + `sensors.processes` 설정으로 코어가 센서 프로세스를 자동 실행
- 현재 run4 기준 기본 등록:
  - `sensors.os.windows_foreground`
  - `sensors.os.windows_idle`
  - `sensors.os.file_watcher`

## 17) 암호화 키 파일 자동 로드
- `encryption.key_path` 지원 추가
- `secrets/collector_key.txt`에 키 저장 시 자동 로드
- 환경변수가 없어도 암호화 동작 가능

## 18) 브라우저 상세 수집 확장
- `browser_extension/content.js`로 본문/요약 추출
- payload에는 `content_summary`만 남기고
- full content는 `raw_json`에만 저장 (암호화 ON 기준)

