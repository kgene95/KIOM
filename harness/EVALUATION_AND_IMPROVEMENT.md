# 범용 하네스·에이전트 평가 및 수정보완 절차

## 목적

이 문서는 NP, docking, MD, 문헌, 논문, 웹앱 등 모든 분야의 하네스와 에이전트를 평가하고 개선하는 공통 절차다. 특정 분야의 결과, 오류, 수치, provider 이름은 이 문서에 기록하지 않는다.

## 평가 순서

1. 목표·범위·완료 조건 확인
2. 총괄→워커 호출 기록과 이벤트 순서 확인
3. 입력·출력·artifact·provenance 확인
4. 상태 전이·의존성·병렬 실행 확인
5. 실패 재현 테스트 작성
6. 원인 분류: 범용 제어층, 분야 adapter, worker, connector, 웹앱 표시
7. 해당 층을 수정하고 회귀 테스트 실행
8. 재시작·재시도·중단·네트워크 실패 검증
9. 사용자 보고와 웹앱·heartbeat 반영 확인
10. 통과 후에만 다음 작업 재개

## 실패 처리 원칙

- 실패를 단순 대기로 숨기지 않는다.
- 재시도 가능 여부와 다음 시각을 기록한다.
- 같은 실패를 정해진 횟수 이상 반복하지 않는다.
- 총괄은 실패 원인과 다음 행동을 알림으로 남긴다.
- 외부 승인·보안 차단·사용자 입력이 필요한 경우 정확한 재개 조건을 기록한다.
- 사용자가 오류를 지적하면 이미 있는 기록을 다시 묻지 않고 해당 분야와 구성요소를 찾아 바로 재현한다.

## 기록 위치

범용 규칙은 상위 `HARNESS.md`, `HARNESS_GUIDE.md`, 이 문서에 기록한다. 분야별 규칙은 `harness/NP_HARNESS.md` 같은 adapter 문서에 기록한다. 특정 실행의 평가·오류·수정 이력은 `harness/evaluations/<DOMAIN>/` 아래에만 기록한다.

## 완료 조건

평가는 문서 작성으로 끝나지 않는다. 재현 테스트가 실패에서 통과로 바뀌고, 실제 이벤트 로그·상태 파일·웹앱 표시가 일치하며, 재시작 후에도 같은 결과가 나와야 완료로 판정한다.
# 2026-10-11: NP 실행 후반부 누락 보완

- 발견: 실제 queue가 STRING/enrichment 이후 `manuscript_review`에서 종료되어 Cytoscape·도킹 후보·Methods/Results 초안이 호출되지 않았다.
- 원인: 문서·스킬에만 후반 단계가 있고 `np_agent_queue.py`, `worker_registry.json`, `np_controller.py`의 실행 계약이 불일치했다. 가상 시뮬레이션도 실제 dispatcher 대신 최종 artifact를 직접 생성해 이 결함을 통과시켰다.
- 수정: 6·7·8번 task와 worker registry/dispatcher 연결, legacy run queue migration, Cytoscape TSV parser 수정, `CORRECT_AND_RERUN` bounded retry 변환, 최종 완료 gate 확대.
- 검증: 전체 harness 회귀 테스트 22/22 통과. Cytoscape가 실행되지 않은 환경에서는 `WAITING_EXTERNAL(reason_code=WAITING_CYTOSCAPE_ONLINE)`으로 기록하며 완료로 위장하지 않는다.
- 현재 환경: Cytoscape 설치 폴더는 있으나 Java runtime과 cyREST가 없어 두 실제 run은 Cytoscape 단계에서 대기 중이다. controller와 1분 supervisor는 재개 조건을 감시한다.

