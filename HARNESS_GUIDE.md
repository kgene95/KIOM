# 범용 하네스 운영 지침

## 목차

1. 목적과 범위
2. 핵심 개념
3. 실행 수명주기
4. 질문·계획·트리거
5. workflow와 worktree
6. 병렬 실행
7. 테스트·검증·복구
8. Git·GitHub 완료 절차
9. 상태와 기억
10. 분야별 adapter와 계획 밖 이벤트
11. 진행 보고와 중단 방지
12. 사전 점검
13. 슈퍼파워스 플러그인 라우팅
14. 문제 라우팅과 재발 방지
15. 프로젝트 컨텍스트 격리

## 목적과 범위

하네스는 AI가 목표를 계획하고 실행하고 검증하고 복구하도록 만드는 공통 제어 계층이다. 각 분야와 프로젝트는 adapter로 연결하고, 실행·기억·검증·승인 규칙은 공통으로 사용한다.

## 핵심 개념

- workflow: 작업의 논리적 DAG와 상태 전이
- worktree: Git 작업을 격리하는 실제 파일 공간
- task: 검증 가능한 한 가지 책임
- worker: task를 수행하는 결정적 스크립트 또는 에이전트
- artifact: 검증 가능한 파일·로그·manifest
- gate: 다음 상태로 넘어가기 위한 조건
- checkpoint: 중단 후 재개할 수 있는 영속 상태

workflow와 worktree는 같은 의미가 아니다. 하나의 workflow가 여러 worktree를 사용할 수 있고, 하나의 worktree에서 여러 독립 task를 순차 실행할 수도 있다.

## 실행 수명주기

`INTAKE → CONTEXT_CHECK → QUESTIONS → PLANNED → WORKTREE_READY → RUNNING → TESTING → VERIFYING → REVIEW_REQUIRED → COMMITTED → MERGED → COMPLETE`를 기본 흐름으로 사용한다. 사용자 승인이나 외부 결과가 필요하면 `WAITING_USER` 또는 `WAITING_EXTERNAL`, 오류는 `FAILED_RETRYABLE`, `BLOCKED`, `INVALIDATED`, `BUDGET_STOP`으로 기록한다. 모든 필수 task와 완료 artifact가 검증되면 `IDLE`이 아니라 `COMPLETE`로 기록하고, 별도 후속 workflow가 있으면 `next_action`에 명시한다.

## 질문·계획·트리거

작업 시작 시 프로젝트 상태, 결정 기록, checkpoint, 이전 승인과 현재 요청을 먼저 읽는다. 이미 답이 있으면 다시 묻지 않는다. 목표가 모호하거나 되돌릴 수 없는 외부 작업·삭제·배포·최종 과학 판단이 필요할 때만 질문한다.

인터뷰와 기획이 끝나면 총괄은 사용자에게 최종 목표, 포함·제외 범위, 최종 산출물과 완료 판정 기준을 제시하고 확인받는다. 확인된 목표는 run 계약과 adapter에 기록하며, 중간 단계가 완료되었다는 이유만으로 최종 완료를 선언하지 않는다.

## 요청 해석·추천·실행 확인

사용자가 연구·분석·코딩·외부 제출·파일 변경·설정 변경·에이전트 구성처럼 결과와 방향에 영향을 주는 요청을 하면 즉시 실행하지 않는다. 총괄은 먼저 요청을 자신의 말로 정리하고, 현재 상태와 제약을 확인한 뒤, 자신의 판단에 따른 추천 방향·대안·예상 영향·완료 기준을 제시한다. 사용자가 방향을 확인한 뒤에만 실행 계획과 변경을 적용한다. 단순 조회, 상태 확인, 로그 조사, 재현 테스트와 같이 결과를 변경하지 않는 작업은 바로 수행할 수 있다.

실행 중 오류나 새로운 이벤트로 계획을 바꿔야 할 때도 같은 절차를 적용한다. 원래 목표와 달라지는 변경은 조용히 적용하지 않고 원인, 선택지, 추천안과 재개 조건을 먼저 보고한 뒤 확인받는다. 다만 데이터 손실·보안 노출·중복 외부 제출을 막기 위한 즉시 중지는 확인 없이 수행하고 사후에 보고한다.

## 사용자 질문·의견에 대한 응답

사용자가 질문하거나 의견을 제시하면 먼저 요점을 짧고 명확하게 답한다. 상태를 보고할 때는 원인, 해결책, 담당 주체, 다음 행동까지 함께 제시한다. 필요할 때만 방향이나 다음 진행 사항을 제시한다. 사용자가 “이해가 안 돼” 또는 “상세히 설명해줘”라고 하면 쉬운 말과 단계별 예시로 설명을 확장한다. 사용자의 의견에 무조건 동의하지 말고, 사실·불확실성·총괄의 추천을 구분해 설명한다. 이미 기록된 답은 다시 묻지 않는다.

Skill trigger는 사용자 요청과 adapter의 작업 유형으로 결정한다. 서브에이전트 trigger는 독립 파일·리소스·검증 경계를 가진 task가 둘 이상일 때만 사용한다. 단순 작업은 결정적 스크립트로 처리한다.

## workflow와 worktree

계획 문서와 `workflow.json`을 먼저 만들고, 구현은 승인된 branch/worktree에서 한다. worktree 생성 후 baseline test를 실행한다. 기준 branch에 직접 작업하지 않는다. worktree를 만들 수 없으면 상태에 이유를 기록하고 명시적으로 안전한 대체 방식을 선택한다.

## 병렬 실행

의존성이 없고 파일·GUI·계정·provider를 공유하지 않는 task는 같은 dispatch group으로 실행한다. 공유 resource가 있으면 lock을 사용해 직렬화한다. 병렬 worker의 결과는 독립 artifact로 저장하고 총괄이 검증 후 통합한다.

## 테스트·검증·복구

버그는 `재현 → 실패 테스트 → 최소 수정 → 통과 → 전체 회귀 테스트` 순서를 따른다. 완료는 worker의 말이 아니라 테스트 출력, artifact 존재, SHA, provenance, reviewer verdict, Git 상태로 판정한다. 오류는 원인과 재개 조건을 기록하고 bounded retry만 수행한다.

## 터미널·GUI 실행 원칙

결정적 계산과 반복 작업은 터미널·API·스크립트를 기본 실행 경로로 사용한다. 입력, 파라미터, 버전, 로그와 artifact를 저장해 재현성과 저비용 장기 실행을 보장한다. GUI는 네트워크 배치, 레이아웃, 그림 품질처럼 시각 확인이 필요한 검수에 사용하며, GUI에서만 수행한 작업은 완료 근거로 삼지 않는다. GUI 프로그램이 필요한 경우에도 단일 Controller가 실행을 소유하고 GUI는 같은 자원을 동시에 조작하지 않는다.

## Git·GitHub 완료 절차

`plan → worktree → implement → test → verify → commit → review → merge → merge 후 재검증 → changelog/state 갱신` 순서다. commit과 merge는 별도 상태다. 외부 전송·삭제·배포·논문 최종화는 승인 게이트를 거친다.

## 상태와 기억

공통 상태는 `PROJECT_STATE.md`, 결정은 `DECISIONS.md`, 실행은 `logs/execution.jsonl`, handoff는 manifest로 저장한다. 대화 기억만으로 재개하지 않는다. 건강한 장기 작업 중에는 조용히 polling하고 완료·실패·중단·사용자 행동 필요 때만 알린다.

## 분야별 adapter

adapter는 domain별 task 목록, 입력·출력 계약, 검증 방법, 외부 connector와 완료 조건을 제공한다. 범용 지침에는 특정 domain의 이름·provider·파일 형식·세부 worker 번호를 넣지 않는다. 각 프로젝트는 자신의 adapter와 skill을 추가로 읽는다.

프로젝트 고유 정보는 프로젝트 폴더의 `<PROJECT_NAME>.md`에 둔다. 여기에는 입력 성분·질환·실험 조건·프로젝트별 용어·수치·문헌·최종 보고서 형식·예외 사례를 기록한다. 범용 하네스와 domain adapter는 프로젝트 파일을 실행 전에 읽고, 프로젝트 파일의 값을 범용 용어와 섞지 않는다. 프로젝트 파일을 찾지 못하면 프로젝트 고유 판단을 시작하지 않고 `PROJECT_CONTEXT_MISSING`을 기록한다.

### 프로젝트 컨텍스트 격리 규칙

하위 분석이나 새 분야 하네스·에이전트를 만들 때마다 프로젝트별 `<PROJECT_NAME>.md`를 먼저 만들고, 프로젝트 고유 정보를 그 파일에서만 관리한다. 범용 하네스와 범용 domain adapter는 다음의 범용 용어만 사용한다.

- 역할: controller, agent, worker, verifier, event router
- 상태: READY, RUNNING, WAITING, FAILED, RETRY, DONE, BLOCKED
- 계약: input, output, artifact, manifest, hash, provenance, gate, handoff
- 절차: intake, simulation, dispatch, validation, recovery, review, report

범용 문서에는 특정 소재명·질환명·CID·실험 marker·provider별 파일명·특정 숫자·프로젝트 예외·특정 agent 번호를 넣지 않는다. 그런 값이 발견되면 프로젝트 파일로 이동하고 범용 문서에는 `<COMPOUND>`, `<DISEASE>`, `<PROJECT_ID>`, `<INPUT_SET>`, `<PROJECT_NAME>.md` 같은 자리표시자를 사용한다. 새 하네스가 프로젝트 파일을 읽지 못하면 고유 분석을 실행하지 않고 `PROJECT_CONTEXT_MISSING`으로 중지한다.

프로젝트 파일의 우선순위는 `범용 하네스 → 분야 adapter → 프로젝트 Markdown → run manifest`이며, 하위 문서가 상위 범용 계약을 완화하거나 덮어쓸 수 없다. 프로젝트 파일을 변경하면 변경 이력과 재검증 결과를 함께 기록한다.

외부 provider adapter는 일반적으로 `SUBMITTED(reference)` → `CHECK_PENDING`/`CHECK_RUNNING` → `CHECK_COMPLETED` → `RAW_DOWNLOADED_AND_VERIFIED` 순서를 사용한다. 식별자·입력 hash·원본 hash가 일치할 때만 다음 task를 깨운다. domain별 상태명과 조회 방법은 해당 adapter에만 기록한다.

### 외부자료·계획 밖 이벤트 라우팅

새 분석 run은 실제 외부 호출 전에 오프라인 시뮬레이션을 실행한다. 정상 입력, 잘못된 식별자 자료, 재업로드, worker 실패·재시작, 최종 artifact 생성을 포함해야 하며, 통과하지 못한 run은 실데이터 분석으로 승격하지 않는다.

시뮬레이션은 계획·구성 직후 별도의 가상 run으로 실행한다. 먼저 실제로 예상한 workflow와 동일한 task·의존성·worker·handoff를 만들고, 정상 입력만 넣어 목표의 마지막 artifact까지 도달하는지 확인한다. 그 다음 workflow가 진행되는 중간 지점에 계획 밖 사용자 이벤트, 외부자료 도착, 형식 오류, 식별자 불일치, 중복 업로드, 네트워크 실패, worker 중단과 재시작을 순서대로 주입한다. 각 이벤트에서 event router가 원본을 보존하고 검수·격리·재맵핑·수신 worker 전달·총괄 보고를 수행하는지 확인한다. 오류가 발생하면 원인을 기록하고 자동 복구 또는 재시도한 뒤, 실패 task만 재개되는지와 독립 task가 계속되는지 확인한다. 마지막으로 목표 artifact, provenance, event log, QC, 의사결정·추천 산출물, 요약 보고서와 완료 상태가 모두 생성될 때만 시뮬레이션을 통과시킨다. 계산 결과가 있어도 추천·보고서·핵심 전달물이 빠지면 `INCOMPLETE`로 남긴다. 발견한 결함과 수정 사항은 회귀 테스트와 adapter 문서에 반영한 뒤 같은 시나리오를 다시 실행한다.

외부 파일, 메일 첨부, 외부 서비스 결과, 사용자 추가 요청처럼 계획된 DAG에 없던 입력은 현재 task에 임의로 섞지 않고 별도 event/task로 기록한다. 총괄은 `event_router` 역할을 호출해 원본 보존 → 출처·형식·식별자·SHA·중복 검수 → domain과 수신 worker 결정 → 표준 변환·재맵핑 → 수신 worker handoff → 총괄 보고 순서로 처리한다. 검수 결과와 route report는 영속 artifact로 남기고, 수신 worker가 실제 재실행한 결과까지 확인하기 전에는 완료로 표시하지 않는다. 입력이 손상되거나 계약과 맞지 않으면 삭제하지 않고 격리하여 `CORRECT_AND_RERUN`으로 기록하며 독립 branch는 계속한다.

파일·형식·식별자·hash를 확인하는 **경계 검증**과 domain의 과학적·업무적 타당성을 확인하는 **독립 QC**는 서로 다른 gate다. 경계 검증이 통과하면 수신 worker의 입력 task를 자동으로 깨우고, 독립 QC가 남아 있다는 이유로 이미 확보된 외부자료를 계속 `미확인` 상태에 두지 않는다. 반대로 경계 검증이 실패하면 domain 분석을 완료로 승격하지 않는다.

## 진행 보고와 중단 방지

실제 작업 중 오류로 최종 목표에 도달하지 못하면 수정된 계약·큐·워커로 실패 지점부터 최종 목표까지의 빠른 가상 시뮬레이션을 먼저 재실행한다. 시뮬레이션이 통과한 뒤에만 실제 run을 해당 checkpoint에서 재개한다.

채팅 보고와 상태 전이는 [PROGRESS_REPORTING.md](PROGRESS_REPORTING.md)를 따른다. 총괄은 run 생성, worker 시작·완료, 승인·외부 대기, 오류·재시도·QC, 완료·예산 중지 시 한국어로 현재 상태와 다음 행동을 보고한다. 한 task가 막혀도 독립 task를 계속 실행하며, 필수 task가 막힌 경우에만 최종 gate를 보류한다.

## 사전 점검

작업 시작 전 [PREFLIGHT_CHECKLIST.md](PREFLIGHT_CHECKLIST.md)를 읽고 전체 workflow, 필요한 Skill·plugin·connector·로컬 프로그램·이메일·권한과 사용자 선행 작업을 한 번에 확인한다. 사용자가 직접 해야 하는 항목은 최우선순위로 미리 고지하고 상태를 기록한다. 사전 점검이 끝나기 전에는 장시간 실행을 시작하지 않는다.

## 슈퍼파워스 플러그인 라우팅

슈퍼파워스 플러그인은 하네스·에이전트·웹앱의 **기획과 소프트웨어 작업 절차**에 우선 검토한다. 작업의 복잡도와 위험을 먼저 판단한 뒤 필요한 경우에만 호출한다. 단순한 문서 수정, 결정적 파일 검사, 상태 동기화, 단일 명령 테스트에는 호출하지 않는다. 작업 유형에 따라 다음 순서로 라우팅한다.

- 새 기능·하네스·에이전트 설계: `superpowers:brainstorming` → `superpowers:writing-plans`
- 구현·수정: `superpowers:executing-plans` 또는 독립 task가 여러 개일 때 `superpowers:subagent-driven-development`
- 버그·반복 중단·예상 밖 동작: `superpowers:systematic-debugging`
- 기능·버그 수정 테스트: `superpowers:test-driven-development` 및 재현→실패→수정→통과 회귀 순서
- 완료 전: `superpowers:verification-before-completion`, 필요 시 `requesting-code-review`와 `finishing-a-development-branch`
- 새 Skill 작성·수정: `superpowers:writing-skills`

슈퍼파워스는 domain의 과학적·업무적 판단을 소유하지 않는다. 해당 판단은 선택된 domain skill과 독립 QC가 담당한다. 플러그인이 연결되지 않았거나 호출 검증 전이면 상태를 `AVAILABLE_UNVERIFIED`로 기록하고 동일한 문서화 절차를 수동으로 유지한다.

### 적용 판단

장점은 요구사항 누락 감소, 계획·구현·테스트의 분리, 재현 가능한 디버깅, 완료 전 검증 강제, 여러 독립 task의 병렬화다. 단점은 짧은 작업에도 절차와 토큰이 늘어날 수 있고, 이미 안정된 domain Skill과 책임이 겹치며, 작은 변경에 subagent를 사용하면 조정 비용이 커진다는 점이다. 따라서 변경 범위가 여러 파일·역할·검증 단계를 포함하거나 버그 재현·회귀 테스트가 필요할 때 적용하고, 한 파일의 명확한 수정이나 결정적 스크립트 실행에는 적용하지 않는다.

## 문제를 발견했을 때의 범용 라우팅

총괄은 문제를 발견한 뒤 멈추거나 사용자에게 원인 조사를 떠넘기지 않는다. `harness/domain_registry.json`에서 domain을 찾고, 범용 계약 검증 → 분야 adapter/worker/skill 확인 → 재현 테스트 → 수정 → 분야 테스트 → 통합·웹앱 상태 반영 → 다음 작업 재개 순서로 처리한다. 해결이 외부 승인·보안 정책에 막히면 실패 원인, 시도한 조치, 필요한 승인, 재개할 작업 ID를 즉시 기록하고 보고한다. 평가 보고서와 과거 로그는 실행 지침이 아니다.

평가·수정보완 절차의 범용 기준은 harness/EVALUATION_AND_IMPROVEMENT.md에 있으며, 특정 분야의 평가 기록은 harness/evaluations/<DOMAIN>/ 아래에만 저장한다.


## 야간 실행과 재발 방지

`harness/run_supervisor.ps1`는 1분 주기로 heartbeat·무진척·실패 작업을 점검한다. 수정이 반영된 뒤에는 해당 task를 실제로 재수행하고, 새 event log와 artifact를 확인한 뒤에만 복구 완료로 판정한다. worker·task 완료나 의미 있는 상태 전이는 완료된 작업과 다음 분석을 보고한다. 오류 해결·재수행·상태 변화가 5분 이상 없을 때만 사용자에게 원인과 다음 행동을 보고하며, 정상 polling이나 worker 진척 중에는 불필요한 보고를 하지 않는다. 승인·보안 차단은 자동 반복하지 않고 재개 조건을 보고한다.


## 증거 통합형 후반부 작업 패턴

분석 결과가 생성되었다고 최종 산출물을 바로 만들지 않는다. 총괄은 (1) 외부·실험·사용자 추가 자료 검수, (2) 원자료와 계산 결과의 증거 통합, (3) 시각화·요약 산출물 생성, (4) 의사결정 후보 추천, (5) 보고서 초안 작성의 순서를 정의하고 각 단계의 산출물과 검증 상태를 다음 담당자에게 전달한다.

각 단계는 독립 worker로 분리할 수 있으며, 같은 영역의 여러 worker를 하나의 agent가 소유할 수 있다. 중요한 것은 agent 번호가 아니라 입력 계약, output manifest, handoff event, 재시도 조건이다. 수치·근거가 부족하면 시각화나 추천을 완료로 표시하지 않고 `WAITING_EXTERNAL` 또는 `CORRECT_AND_RERUN`으로 되돌린다. 전체 원자료와 전체 계산 결과는 보존하고, 본문 표시용 요약은 선택 규칙과 제외 이유를 기록한다.

## Project-root review package

At project setup, create a collaborator review package under the project root. Use five data boundaries: 01_raw (verified collected inputs), 02_calculated (normalization, mapping, overlap), 03_external_analysis (provider-generated PPI and enrichment), 04_visual_qc (Cytoscape inputs, topology, MCODE and visual checks), and 05_figures_reports (figures, candidate rationale, Methods/Results and reports). The package README must record the complete inventory and input -> analysis -> output extension for each file. Do not include invalid or superseded data.

The review package README uses a table for the file inventory. Each row records folder, file, input/source, analysis or transformation, output extension, and collaborator-review purpose. A prose explanation may follow the table but does not replace it.

Before Methods/Results are finalized, the review package must include a reproducibility metadata file with tool versions, provider/database release, parameters, dates, hashes, and script revision. Missing metadata must be reported as a limitation rather than guessed.
