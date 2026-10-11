# 하네스·에이전트 전체 감사 보고서

감사일: 2026-10-11 (Asia/Seoul)  
대상: `KIOM/harness`, `KIOM/agents`, `KIOM/CODEX`, NP adapter와 로컬 대시보드

## 감사 결론

현재 구성은 문서상 원칙은 갖추었지만, 실제 실행 계약이 하나로 고정되어 있지 않다. 그래서 worker가 준비되어도 dispatch에서 제외되거나, controller가 살아 있어도 실질 작업이 진행되지 않는 문제가 발생했다. 현재 분석 결과를 더 진행하는 것보다 아래 구조 결함을 먼저 고치는 것이 우선이다.

## 심각도 높은 결함

### P0. 실행 경로가 두 개다

- 문서는 `runner.py`와 `worker_registry.json`을 단일 진입점으로 정의한다.
- 실제 장기 실행은 `run_controller.ps1 → np_controller.py → TASK_WORKERS`를 사용한다.
- `np_controller.py`는 registry를 읽지 않고 자체 매핑을 사용한다.
- `dispatcher.py`는 별도 경로이며 worker 결과를 항상 `DONE`으로 감싸는 문제가 있다.

결과: 문서의 “등록된 worker만 실행” 규칙과 실제 실행이 일치하지 않는다.

### P0. 단일 controller 보장이 없다

동일 run에 controller lock 또는 lease가 없다. 실제로 동일 포트·컨트롤러가 여러 개 생길 수 있는 상태였다.

필수 수정:

- run별 `controller.lock` 또는 Windows mutex
- 소유 PID, 시작 시각, lease 만료, heartbeat 기록
- 두 번째 controller는 실행하지 않고 `DUPLICATE_CONTROLLER` 이벤트 기록

### P0. 죽은 worker 복구가 없다

`RUNNING` task가 프로세스 종료 후에도 계속 `RUNNING`으로 남으면 `ready_tasks()`가 다시 선택하지 않는다.

필수 수정:

- task에 `started_at`, `lease_until`, `worker_pid`, `attempt_id` 저장
- lease 만료 시 `ORPHANED → RETRY_WAIT` 전환
- 재개 시 입력 hash와 attempt id를 확인

### P0. registry와 실제 구현 상태가 불일치한다

registry에는 `sea_submit`, `pharmmapper_submit`, `pharmmapper_check_job`, `gmail_job_monitor`, `normalize_targets`, `overlap_analysis` 등이 계획 또는 함수 등록으로 남아 있다. 일부는 실제 callable이 없거나 controller에서 호출되지 않는다.

필수 수정:

- registry를 실행 전 import·callable·signature 검증
- `planned`, `implemented`, `verified`, `disabled` 상태를 분리
- `implemented`라고 쓰려면 최소 dry-run·실패 주입·재시작 테스트를 통과
- controller는 registry 외부의 하드코딩 매핑을 사용하지 않음

## P1. 상태·실패·재시도 결함

### P1. 상태 전이가 코드와 문서에서 다르다

`DONE`, `DONE_RAW_UNVERIFIED`, `WAITING_MAPPING_QC`, `WAITING_EXTERNAL`, `READY_FOR_WORKER`, `RETRY_WAIT`가 여러 파일에 분산되어 있고 전이 표가 없다. 이번에도 `DONE_RAW_UNVERIFIED`를 의존성 충족으로 보지 않아 다음 worker가 실행되지 않았다.

필수 수정:

- `WORKFLOW_SCHEMA.md`에 모든 상태와 허용 전이를 단일 표로 정의
- 상태 전이는 한 함수에서만 수행
- 잘못된 전이는 즉시 `STATE_CONTRACT_ERROR`로 기록

### P1. retry가 bounded이지만 재개 시각이 없다

`attempts`는 있으나 `next_attempt_at`, backoff, 오류 분류, 마지막 시도 이유가 일관되게 저장되지 않는다. 일부 `WAITING_EXTERNAL`은 다시 시도하지 않고, 일부 retry 상태는 반복 호출될 수 있다.

필수 수정:

- `retry_policy`: max attempts, exponential backoff, jitter, retryable error class
- `next_attempt_at` 이전에는 worker를 호출하지 않음
- 한도 초과 시 `BLOCKED`와 사용자 알림 생성

### P1. worker 산출물 검증이 dispatcher에 강제되지 않는다

문서에는 output contract와 SHA가 있지만 현재 dispatcher는 worker 반환값만 보고 상태를 갱신한다. `DONE`에 필요한 artifact 존재·SHA·provenance 검증이 중앙에서 강제되지 않는다.

필수 수정:

- worker는 `RESULT`만 반환
- verifier가 output contract·파일·SHA·입력 hash·run id를 검증한 뒤 `DONE` 선언
- 실패 시 `CORRECT_AND_RERUN` 또는 `BLOCKED`

## P1. 외부 provider·Gmail 계약의 허위 완료 위험

문서에는 SEA/PharmMapper/Gmail 흐름이 자세히 적혀 있으나 registry와 실제 worker 구현 상태가 `planned`인 항목이 남아 있다. 문서에 기능이 있다고 해서 connector가 연결된 것으로 판정하면 안 된다.

필수 수정:

- connector별 `AVAILABLE_UNVERIFIED → CONNECTED → VERIFIED → DEGRADED` 상태
- 연결 검증 테스트를 통과하기 전에는 자동 실행 대상에서 제외
- CAPTCHA, 로그인, 이메일, 외부 제출은 provider별 승인 정책을 코드에 반영

## P2. 총괄·웹앱·보고 문제

- heartbeat는 controller가 반환한 pre-dispatch 상태를 표시할 수 있었다.
- 프로젝트에 연결되지 않은 실제 run은 기존 웹앱 목록에서 보이지 않았다.
- 채팅 보고는 파일 이벤트와 자동 연결되지 않아 사용자가 물어봐야 상태가 드러났다.
- 정상 polling과 의미 있는 이벤트 보고의 주기·조건이 문서화되어 있으나 자동 알림 구현은 없다.

필수 수정:

- heartbeat는 post-dispatch 상태와 `last_event_id`를 기록
- 웹앱 index에 실제 live run을 표시하고 stale heartbeat를 경고
- `worker_started`, `worker_completed`, `worker_waiting`, `worker_failed`, `orphan_recovered`, `blocked`를 사용자 보고 이벤트로 정의

## P2. Git·worktree·변경 이력 문제

- 범용 문서는 worktree와 commit·merge를 요구하지만 이번 변경은 기준 checkout에 직접 남아 있다.
- 현재 변경에는 이전 사용자 작업과 이번 하네스 변경이 섞여 있어 일괄 commit하면 안 된다.
- `DECISIONS.md`의 위치가 문서마다 다르고 `CODEX/ChatGPT.md`가 참조하는 일부 파일은 누락될 수 있다.

필수 수정:

- 하네스 자체 변경용 worktree/branch
- 변경 목록과 테스트 결과를 분리한 commit
- merge 후 controller·웹앱·worker smoke test
- 존재하지 않는 문서 참조를 preflight에서 실패 처리

## 재발 방지용 목표 구조

```text
단일 controller
  ├─ run lock / lease
  ├─ event reducer
  ├─ state transition validator
  ├─ registry validator
  ├─ dependency scheduler
  ├─ bounded retry / orphan recovery
  ├─ artifact verifier
  └─ heartbeat + user event reporter

domain adapter (NP)
  ├─ task DAG
  ├─ worker registry entries
  ├─ input/output contracts
  ├─ provider connector gates
  └─ scientific QC gates

webapp
  └─ read-only projection of the same durable state
```

## 승격 전 필수 검증

1. registry의 모든 `implemented` 항목 import·signature 검증
2. 두 controller 동시 시작 시 하나만 실행
3. worker를 강제 종료하면 lease 만료 후 자동 복구
4. worker가 예외를 내면 retry/backoff/차단/알림 확인
5. `DONE_RAW_UNVERIFIED`에서 다음 QC worker가 실제 호출됨
6. 입력 hash 변경 시 downstream만 `INVALIDATED`
7. 외부 provider connector가 끊기면 다른 독립 branch는 계속 실행
8. 웹앱과 live monitor가 동일 run의 post-dispatch 상태를 표시
9. 새 프로세스에서 checkpoint를 읽어 재개
10. 전체 회귀 테스트와 dry-run 후에만 commit/merge

## 현재 판단

현재 하네스는 “상태 파일을 남기는 프로토타입”에서 “재시작 가능한 실행 시스템”으로 승격되는 중이다. 문서만 보완해서는 재발을 막을 수 없으며, P0 항목인 단일 실행 경로·lock/lease·registry 검증·orphan recovery를 먼저 구현해야 한다. 그 후 NP의 mapping, PPI, 외부 provider worker를 다시 연결해야 한다.

## 2026-10-11 시행 검증 결과

- 최신 컨트롤러/하네스/워커 문법 검사: 통과
- 하네스 회귀 테스트: 15/15 통과
- NP 대시보드 테스트: 23/23 통과
- 등록 워커 로딩: 6개 callable 확인 (`initial_ppi` 포함)
- 단일 워커 smoke test: DONE·artifact·worker_started/worker_completed 이벤트 확인
- 5-agent 분담 검증: agent1~agent5 독립 작업 5개를 모두 DONE 처리하고 이벤트 10개 기록
- 실행 중인 두 NP run: 컨트롤러 PID와 장기 lease 파일 확인, 두 번째 컨트롤러의 중복 실행은 `ControllerBusy`로 차단
- orphan recovery/재시도/산출물 없는 DONE 거부: 회귀 테스트로 통과
- 실제 두 run의 현재 병목: `initial_ppi`가 UniProt 미확인 14개/16개로 `WAITING_EXTERNAL`; 이후 final_ppi/QC/manuscript는 의존성 때문에 대기 중
- SEA·PharmMapper 재제출은 현재 검증 단계에서 재실행하지 않음. 기존 결과는 저장되어 있고, submit worker는 승인·외부 CAPTCHA/사이트 상태를 포함하므로 별도 connector 검증 게이트로 유지

### 남은 보완 게이트

1. 상태 전이 변경을 단일 함수로 강제하는 코드 보완
2. 실제 Gmail 수신·SEA 완료·PharmMapper job ID 확인을 포함한 connector 통합 테스트
3. UniProt 미확인 ID 보정/재시도 후 최종 PPI→QC→원고 단계 재개
- 상태 전이 guard 추가 후 회귀 테스트: 16/16 통과. `QUEUED→RUNNING` 같은 우회 전이는 거부하고, 준비→실행→완료 경로만 허용
