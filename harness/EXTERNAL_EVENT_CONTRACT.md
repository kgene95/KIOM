# 외부자료·추가 이벤트 공통 계약

## 적용 범위

사용자 업로드, Gmail 수신, provider 결과 다운로드, 로컬 파일 생성, 웹앱 입력은 모두 `EXTERNAL_DATA_RECEIVED` 이벤트로 취급한다.

## 총괄 처리 절차

1. 파일 또는 이벤트를 원본 그대로 보존한다.
2. 파일명·경로·크기·SHA-256·수신 시각·출처·관련 run을 기록한다.
3. 파일 형식과 schema를 검사한다.
4. domain registry에서 담당 adapter와 변환 worker를 선택한다.
5. 원본을 분석용 표준 형식으로 변환하고 변환 결과의 provenance와 hash를 기록한다.
6. 원본·변환본·검증 결과를 연결한 handoff manifest를 만든다.
7. 영향받은 task만 `INVALIDATED` 또는 `READY_FOR_WORKER`로 전환한다.
8. 변환·입력·QC worker를 자동 호출한다.
9. 실패하면 `FAILED_RETRYABLE`과 다음 행동을 기록하고, 반복 한도 초과 시 총괄에 알린다.
10. 성공하면 downstream 의존성을 다시 계산하고 즉시 다음 작업을 dispatch한다.

## 종료 금지 조건

새 외부자료가 감지됐는데 파일 형식이 맞지 않는다는 이유만으로 전체 run을 종료하지 않는다. 변환 가능한 경우 변환하고, 변환 불가인 경우 필요한 형식·오류 행·담당 worker·사용자 조치를 기록한 뒤 독립 작업을 계속한다.

## 완료 조건

원본 저장, 변환본 생성, hash/provenance 기록, schema QC, 영향 task 재계산, 이벤트 로그, 웹앱·heartbeat 반영이 모두 확인되어야 외부자료 처리가 완료된다.

## 워커 간 외부자료 알림 계약

모든 외부자료 이벤트는 `external_data_intake` 검수 worker를 먼저 거친다. 검수 worker는 `EXTERNAL_DATA_VALIDATED`, `recipient`, 원본·변환 artifact, SHA-256, CID 판정, 다음 행동을 `worker_notifications.jsonl`에 남긴다. 수신 worker는 이를 읽고 입력 manifest와 hash를 갱신한 뒤 재실행한다. 알림이 확인되지 않은 상태에서는 이전 결과를 재사용하거나 조용히 대기하지 않는다.
