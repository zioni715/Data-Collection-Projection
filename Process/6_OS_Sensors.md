# 6. OS Sensors
**목표:** OS 기반으로 “앱/창/유휴/파일” 흐름 이벤트가 자동으로 들어오게 한다.  
이 단계가 되면 사용자가 PC를 쓰기만 해도 events가 쌓인다.

---

## 6.1 산출물
- foreground(app/window) 센서
- idle 센서
- file watcher 센서
- 센서 → 코어 ingest(HTTP/pipe) 전송

---

## 6.2 구현 우선순위(권장)
### 1) Foreground 앱/창 감지(가장 중요)
- 0.5~1초 폴링(또는 이벤트 훅 가능 시 이벤트 기반)
- 변화가 있을 때만 emit
- 2초 미만 전환은 코어에서 debounce로 드롭

**이벤트 예**
- foreground_changed
- app_focus_block (코어에서 블록화해도 됨)

### 2) Idle 감지(세션 경계)
- idle_start / idle_end
- idle 임계값은 우선 10~15분부터 시작(조정 가능)

### 3) File watcher(산출물/문서 흐름)
- 파일 생성/수정/이동 감지
- 경로 원문은 코어에서 해시 처리(센서는 최소로만)

---

## 6.3 센서 이벤트 payload 가이드
### foreground_changed
- app: 프로세스명/앱명
- window_title: (가능하면) 제목(코어에서 마스킹)
- pid, window_id(핸들이면 문자열로 전달 가능 → 코어가 해시)

### app_focus_block
- duration_sec: 유지 시간
- app, window_id

### idle_start/idle_end
- idle_threshold_sec

### file_changed
- action: created/modified/moved/deleted
- path(원문 전달이 필요하면 “로컬 only”로만, 코어에서 해시 저장)

---

## 6.4 통합 테스트
- [ ] 센서 실행 → 코어로 이벤트가 들어온다
- [ ] PC에서 앱 전환/유휴/파일 저장 시 events가 증가한다
- [ ] focus block이 정상적으로 압축되어 저장된다(이벤트 폭주 없음)

---

## 6.5 다음 단계
OS 흐름은 확보됐다. 이제 “의미 이벤트”를 위해 **Add-in/Extension 수신**을 붙인다(6단계).
