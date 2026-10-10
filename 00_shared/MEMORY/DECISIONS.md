# Project decisions

## 2026-10-10 — Generic harness before domain rebuild

- status: accepted
- decision: 범용 하네스와 공통 에이전트 계약을 먼저 구성하고, 기존 NP 분석 에이전트는 `NP_ADAPTER`로 연결한다.
- rationale: 앞으로 NP·docking·MD·문헌·논문·웹앱에 같은 실행 제어가 필요하다. 도메인 에이전트를 먼저 고치면 실행·승인·재시작·비용·검증 규칙이 다시 중복될 위험이 있다.
- scope: generic runner, task DAG, event log, approval gates, retries, checkpoints, model/cost policy, skill audit, cross-device memory, worker registry.
- provider assumption: 사용자가 Gmail·SEA·PharmMapper 자동 연결을 이미 구성했으므로 기존 connector/adapter 자산을 보존하고 하네스 이벤트에 연결한다. 연결 상태는 실행 시 검증한다.
- next: generic harness 계약 검증 → NP adapter 연결 → provider event와 Gmail 결과 수신 회귀 테스트 → NP 전체 run 검증.
