# 7. Add-in and Extension Receiver
**목표:** Excel/Outlook/Browser/IDE 등에서 “의미 이벤트”를 코어로 받아 동일 파이프라인으로 처리한다.  
(Add-in 자체 개발과 별개로, 수신기/표준화가 이 단계의 핵심)

---

## 7.1 산출물
- add-in 이벤트 수신 endpoint(HTTP 권장)
- event_type 표준화(Excel/Outlook 최소 세트)
- OS 이벤트와 같은 스키마로 저장됨 확인

---

## 7.2 우선순위: Excel / Outlook 최소 이벤트 세트
### Excel (예)
- workbook_opened
- refresh_pivot, refresh_query
- export_pdf, export_csv
- chart_copied
- save_as

### Outlook (예)
- compose_started
- attachment_added_meta (count, size_total, file_exts)
- recipients_selected_meta (hash/group_id)
- send_clicked  ← 세션 종결 트리거로 매우 중요

---

## 7.3 수신기(Receiver) 설계 포인트
- 로컬 only: `127.0.0.1`
- 인증이 필요하면: shared token 헤더(추후)
- 배치 전송(list) 지원하면 효율 좋아짐
- 실패 시에도 코어가 죽지 않도록 예외 처리

---

## 7.4 테스트 방법(가장 빠른 형태)
- curl로 Excel/Outlook 이벤트 샘플 JSON을 직접 주입
- 저장된 events에서 priority/프라이버시/스키마가 동일하게 적용되는지 확인

---

## 7.5 다음 단계
이제 이벤트가 충분히 모인다. 다음은 원장을 “업무 단위”로 묶는 **세션화**(7단계).
