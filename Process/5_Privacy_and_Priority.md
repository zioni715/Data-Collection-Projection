# 5. Privacy and Priority
**목표:** 수집 프로그램이 안전하게 동작하도록 **프라이버시 가드 + 우선순위/샘플링**을 코어 파이프라인에 붙인다.  
이 단계가 완료되면 “계속 돌려도 괜찮은 수집기”가 된다.

---

## 5.1 산출물
- Privacy Guard 적용(해시/마스킹/denylist)
- Priority 분류(P0/P1/P2)
- Drop/Sampling 규칙(디바운스, short-focus 드롭, focus-block 압축)

---

## 5.2 프라이버시 정책(권장 기본값)
### 1) Content 수집 금지
- 문서 본문/메일 본문/셀 값/키 입력/스크린샷은 수집하지 않음
- payload에는 메타만 넣는 규칙을 팀 기준으로 고정

### 2) 식별자 해시 처리
- window_id, resource_id 등은 **항상 해시(HMAC-SHA256 + salt)** 로 저장
- 원문 매핑이 필요하면 로컬 vault에만(암호화 권장)

### 3) 창 제목/텍스트 마스킹
- 길이 제한(예: 80자)
- 패턴 마스킹(이메일/전화/긴 숫자열)
- 필요하면 “denylisted 앱”에서는 payload 자체를 드롭

### 4) allowlist/denylist
- password manager/금융앱 등은 deny 권장
- 조직 정책상 allowlist 모드도 지원 가능(허용 앱만 수집)

---

## 5.3 우선순위(P0/P1/P2) 설계
### P0: 절대 보존(업무 종결/결과)
예)
- send_clicked
- export_pdf
- file_saved
- refresh_pivot

### P1: 중요 신호(업무 흐름)
예)
- file_opened
- compose_started
- workbook_opened
- app_focus_block(압축 블록)

### P2: 노이즈 가능(샘플링/드롭 대상)
예)
- window_title_changed 빈번 이벤트
- 짧은 탭 전환
- clipboard meta

---

## 5.4 샘플링/드롭 규칙(경량화)
- **Debounce:** 2초 미만 전환은 기록하지 않기(노이즈 컷)
- **Focus Block:** 포그라운드 유지 시간은 block(duration) 1건으로 압축
- **Buffer pressure:** 큐가 밀리면 P2부터 드롭

---

## 5.5 테스트 체크리스트
- [ ] resource_id/window_id가 DB에 원문으로 남지 않는다
- [ ] window_title이 마스킹/길이 제한을 통과한 형태로 저장된다
- [ ] event_type에 따라 priority가 기대대로 저장된다
- [ ] 짧은 전환 이벤트가 DB에 과도하게 쌓이지 않는다

---

## 5.6 다음 단계
이제 실제 OS 흐름을 자동으로 넣기 위해 **OS 센서**를 연결한다(5단계).
