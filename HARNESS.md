# KIOM Research Harness

## 목차

1. [목적](#목적)
2. [설계 원칙](#설계-원칙)
3. [실행 구조](#실행-구조)
4. [총괄과 세부 에이전트](#총괄과-세부-에이전트)
5. [이벤트와 병렬 실행](#이벤트와-병렬-실행)
6. [승인·외부 서비스·알림](#승인외부-서비스알림)
7. [실패 복구와 재시작](#실패-복구와-재시작)
8. [비용과 모델 라우팅](#비용과-모델-라우팅)
9. [검증과 완료 조건](#검증과-완료-조건)
10. [운영 방법](#운영-방법)
11. [스킬 스택 감사와 평가](#스킬-스택-감사와-평가)

## 목적

이 하네스는 여러 분야에 공통으로 적용되는 실행 제어 계층이다. 작업이 자료 도착이나 외부 작업 완료에서 멈추지 않도록 상태, 의존성, 승인, 재시도, 재시작 조건, 비용 한도를 저장한다. 분야별 해석과 최종 결론은 각 adapter와 독립 QC가 담당한다.

## 설계 원칙

- 저장소 안의 Markdown, JSON schema, 실행 로그와 결과 manifest를 에이전트가 읽을 수 있는 단일 기준으로 사용한다.
- 상태 표시와 실제 실행을 분리한다. `READY_FOR_WORKER`는 실행 대기이며 `DONE`이 아니다. 필수 task와 artifact가 모두 검증되면 Controller는 `IDLE`이 아닌 `COMPLETE`와 후속 `next_action`을 기록한다.
- 독립 작업은 병렬 그룹으로 계획하되 같은 파일·GUI·외부 계정은 단일 컨트롤러만 조작한다.
- 외부 제출, 연결된 메일 서비스 접근, 자동화 방지 확인, 로그인, 기존 자료 재사용, 최종 과학 판단은 승인 게이트로 명시한다.
- 자동 재시도는 일시 오류에만 제한하고, 같은 실패를 무한 반복하지 않는다.
- 모든 사이클은 원자적으로 상태를 저장하고, 중단 뒤 같은 run을 재개할 수 있어야 한다.
- 완료는 경과 시간이 아니라 산출물·검증 로그·독립 QC로 판정한다.

## 인터뷰·기획 완료 게이트

총괄은 인터뷰와 구성 기획이 끝난 시점에 최종 목표, 범위, 목표 산출물, 완료 조건과 중단 조건을 사용자에게 제시하고 확인받는다. 확인된 목표를 run 계약과 분야 adapter에 저장한 뒤에만 시뮬레이션과 실작업을 시작한다.

프로젝트의 고유한 이름·입력·질환·실험 자료·수치·예외·보고서 형식은 반드시 프로젝트 폴더의 `<PROJECT_NAME>.md`에 저장한다. 범용 하네스와 분야 상위 하네스에는 이를 복사하지 않고, 실행 시작 시 프로젝트 파일을 읽어 adapter 설정으로 주입한다.

하위 분석 하네스·에이전트를 새로 만들 때도 같은 규칙을 적용한다. 새 구성은 역할·상태·계약·검증·복구를 범용 용어로 작성하고, 프로젝트별 내용은 새 `<PROJECT_NAME>.md`에만 기록한다. 프로젝트 파일이 없는 상태에서 특정 프로젝트의 수치나 예외를 문서에 직접 삽입하지 않는다.

## 실행 전 의견·추천 확인

결과를 바꾸는 요청을 받으면 총괄은 즉시 실행하지 않고 요청 해석, 현재 상태, 제약, 자신의 추천 방향, 대안과 완료 기준을 먼저 제시한다. 사용자가 추천 방향을 확인한 뒤에만 구현·분석·외부 작업·파일 변경을 시작한다. 조회·상태 확인·진단·재현 테스트는 확인 없이 수행할 수 있다. 진행 중 계획 변경이 필요하면 같은 확인 절차를 다시 적용하고, 데이터 손실·보안·중복 제출을 막기 위한 중지는 즉시 수행 후 보고한다.

## 사용자 대화 응답 규칙

질문·의견에는 핵심 답을 짧고 명확하게 제시하고, 필요할 때만 방향 또는 다음 작업을 덧붙인다. 상태만 전달하고 끝내지 말고 원인, 해결책, 담당 주체와 다음 행동을 함께 제시한다. 사용자가 상세 설명을 요청하면 전문용어를 줄이고 쉬운 말과 순서로 설명한다. 총괄은 사용자의 의견에 자동으로 동의하지 않으며 확인된 사실, 불확실성, 자신의 추천을 구분한다. 같은 질문을 반복하지 않도록 결정과 답변을 상태 기록에서 확인한다.

## 문제 발생 시 분야 라우팅과 보완 루프

범용 하네스는 분야별 내용을 대신 판단하지 않는다. 대신 모든 문제를 다음 순서로 라우팅하고, 해결될 때까지 작업을 종료하지 않는다.

1. 사용자 지적, 오류 로그, 새 파일, 외부 응답, heartbeat 변화를 `INCIDENT` 이벤트로 기록한다.
2. 총괄은 범용 계약·상태·lease·이벤트 로그를 먼저 검사한다.
3. 문제의 `domain`과 `component`를 판정하고 해당 adapter, worker 계약, skill, 웹앱 연결부를 읽는다.
4. 재현 테스트를 만들어 실패를 고정한다.
5. 분야 담당 worker 또는 adapter를 호출해 원인을 수정한다. 독립적인 보완 작업은 병렬로 실행한다.
6. 실패 재현 테스트가 통과할 때까지 수정·재실행한다. 외부 승인이나 보안 차단이면 정확한 재개 조건을 기록한다.
7. 분야 테스트, 통합 테스트, 웹앱 표시, event log를 모두 검증한 뒤에만 다음 작업으로 진행한다.
8. 같은 유형의 재발을 막도록 범용 규칙, 분야 지침, worker 계약 중 올바른 층에 규칙을 반영한다.

총괄은 `FAILED`, `BLOCKED`, `WAITING_USER`, `WAITING_EXTERNAL`을 발견하면 단순히 대기하지 않는다. 원인 분석, 재시도·대체 경로·사용자 알림 중 가능한 다음 행동을 dispatch하고, 행동이 불가능한 경우에도 이유와 재개 조건을 heartbeat와 채팅 보고에 남긴다.

## 실행 구조

`harness/runner.py`가 범용 진입점이고, 분야별 adapter가 task 정의와 산출물 검증을 제공한다. 한 사이클은 다음 순서로 동작한다.

1. run 잠금과 `harness_state.json` 복구
2. 선택된 domain의 큐와 외부 결과 manifest 동기화
3. 이벤트 기록 및 변경 입력 감지
4. 의존성이 충족된 작업의 병렬 dispatch 계획 작성
5. 승인 필요·외부 대기·실행 가능 작업 분리
6. bounded retry와 예산 확인
7. 실행 결과와 다음 재개 조건 원자 저장
8. 완료·실패·필수 사용자 행동만 알림 대상으로 등록

현재 단계의 하네스는 안전한 상태 조정과 dispatch 계획을 먼저 보장한다. 외부 서비스와 문서·메일 연결은 검증된 connector와 별도 승인 후 adapter를 통해서만 실행한다.

## 터미널·GUI 실행 정책

터미널·API·결정적 스크립트를 계산과 자동 복구의 기본 경로로 둔다. 입력·버전·로그·artifact를 고정해 토큰 사용량과 반복 비용을 줄이고 재현성을 높인다. GUI는 결과 네트워크와 그림을 눈으로 확인하는 검수 단계에만 사용한다. 같은 PC·프로그램·파일을 Controller와 GUI가 동시에 조작하지 않으며, GUI가 종료되어도 터미널 경로에서 run을 재개할 수 있어야 한다.

등록된 worker의 입력·출력·실패 계약은 `harness/WORKER_CONTRACT.md`와 `harness/worker_registry.json`에 있다. registry에 없는 임의 명령은 실행하지 않는다.

## 총괄과 분야별 세부 에이전트

| 역할 | 책임 | 입력 | 산출물 |
|---|---|---|---|
| 총괄 에이전트 | 목표, DAG, 승인, 재시작, 비용, 알림 | 사용자 목표와 run 상태 | 실행 상태, dispatch 계획, 다음 행동 |
| 분야 총괄 | 목표, DAG, 승인, 재시작, 비용, 알림 | 사용자 목표와 run 상태 | 실행 상태, dispatch 계획, 다음 행동 |
| 분야 worker | 해당 분야의 입력·계산·외부 연결 | adapter 계약 | 검증된 artifact와 handoff |
| 독립 검증 worker | lineage, 입력 변경 영향, 재실행 판정 | 모든 새 산출물 | PASS, CORRECT_AND_RERUN, BLOCKED |

| 이벤트 라우터 | 계획 밖 자료·추가 업무의 검수, 재맵핑, 담당 worker handoff | 외부자료 이벤트와 추가 요청 | route report, handoff, 총괄 알림 |

역할 이름만 적고 실행된 것으로 간주하지 않는다. 각 역할은 검증 가능한 파일과 상태 전이를 남겨야 한다.

## 이벤트와 병렬 실행

입력 검증, 외부 job ID 생성, 결과 raw 파일 도착, 외부 완료 알림, QC 수정, 사용자 승인과 파일 변경은 모두 이벤트다. 이벤트가 발생하면 총괄은 영향을 받는 작업을 다시 계산한다.

- 서로 독립인 입력 검증·자료 수집·분석은 병렬 실행한다.
- 외부 작업 제출·상태 확인은 각 job의 격리된 작업으로 병렬 실행할 수 있다.
- 한 provider가 지연되어도 검증된 독립 branch는 계속한다.
- 새 raw 입력이 오면 영향받은 downstream만 `INVALIDATED` 후 QC를 거쳐 재실행한다.
- 같은 run의 동일 외부 계정, GUI, 파일 묶음은 병렬 작업이 동시에 조작하지 않는다.

`dispatch_plan.json`에는 cycle, 병렬 그룹, 의존성, 파일 충돌 방지 정보가 남는다.

### 외부자료와 계획 밖 이벤트

새로운 분석을 시작하기 전 가상 입력과 의도적 오류를 사용하는 사전 시뮬레이션을 통과해야 한다. 시뮬레이션은 외부자료 오류 격리, 재업로드 재개, handoff, 후속 artifact 생성을 검증하며 결과와 보완사항을 회귀 기록으로 남긴다.

시뮬레이션은 계획된 workflow를 축약해서 흉내 내는 문서 확인이 아니다. 실제 run과 같은 task·의존성·상태 전이를 만든 뒤 정상 경로를 먼저 완료하고, 중간에 계획 밖 이벤트와 외부자료를 가상으로 주입한다. 자료 도착·오류·중복·식별자 불일치·worker 실패·재시작을 주입한 뒤, 이벤트 라우터의 검수·격리·재맵핑·handoff, 총괄의 재호출·오류 보고, 독립 task의 계속 실행, 최종 목표 artifact 생성을 순서대로 검증한다. 실패 원인과 보완을 회귀 테스트·adapter·변경 이력에 기록하고 재실행해 통과한 경우에만 실제 분석을 시작한다.

실제 작업 중 오류로 최종 목표에 도달하지 못하면 수정 후 실패 지점부터 최종 목표까지의 빠른 가상 시뮬레이션을 다시 실행해 복구 경로를 검증하고, 통과한 뒤 실제 run을 checkpoint에서 재개한다.

외부 파일, 메일 첨부, 외부 서비스의 결과, 사용자 추가 요청처럼 원래 계획에 없던 입력은 현재 task에 조용히 섞지 않고 별도 이벤트와 task로 기록한다. 총괄은 다음 주기를 기다리지 않고 경계 검수 역할을 먼저 호출한다. 경계 검수는 원본 보존, SHA-256, 출처, 형식, 식별자, 중복 및 오염 여부를 확인하고 `external_validation_manifest.json`을 만든다. 검수에 통과한 자료만 domain adapter가 정한 표준 형식으로 변환하고 수신 worker에 handoff한다.

검수 결과와 수신 worker, 다음 행동, 입력 hash는 `worker_notifications.jsonl`과 route report에 기록한다. 수신 worker는 알림을 소비한 뒤 실제 재맵핑·재실행을 수행하고 결과를 반환한다. 총괄은 검수 report와 수신 worker 결과를 모두 확인하기 전에는 branch를 완료로 표시하지 않는다. 검수 실패나 식별자 불일치는 자료를 삭제하지 않고 격리하며 `CORRECT_AND_RERUN`으로 기록한다. 독립 branch는 계속 실행한다.

외부 파일의 경계 검증(출처·형식·식별자·SHA)과 domain의 독립 QC는 별도 gate다. 경계 검증이 통과하면 해당 입력 task를 자동으로 깨우고, 독립 QC 대기 때문에 이미 검증된 외부자료를 계속 미완료로 남기지 않는다. 경계 검증이 실패한 자료만 격리하고 downstream 완료를 차단한다.

## 승인·외부 서비스·알림

다음은 자동 실행하지 않고 `WAITING_USER` 또는 `WAITING_EXTERNAL`로 저장한다.

- 기존 자료 재사용 또는 새 source job 제출
- 연락 이메일 사용, 로그인, 자동화 방지 확인, 이용약관 동의
- raw 연구자료의 외부 전송
- 논문용 최종 결론, docking 후보 확정, 결과 branch 병합

연결된 메일·문서·외부 작업은 실제로 테스트된 connector/heartbeat가 있을 때만 감시한다. 완료 판정은 provider가 제공하는 공식 식별자와 원본 검증 결과로 한다. 메일 미수신만으로 실패를 판정하지 않는다. 본문·주소·토큰은 최소한으로 다루고, 알림은 완료·실패·예기치 않은 중단·사용자 행동 필요 시에만 생성한다.

## 실패 복구와 재시작

각 작업은 `attempts`, `max_attempts`, `last_error`, `resume_condition`, `next_action`, `last_updated_utc`를 가진다.

- 네트워크·일시 오류: 제한된 재시도 후 문서화된 대체 경로를 시도한다.
- 입력/QC 오류: 원인을 고친 뒤 영향받은 하류만 invalidation하고 재실행한다.
- 승인·인증·자동화 방지 확인: 자동 반복하지 않고 정확한 재개 조건을 저장한다.
- 같은 오류가 예산을 넘으면 `BLOCKED`로 종료하고 사용자에게 원인과 필요한 행동을 알린다.
- 프로세스가 끊겨도 `harness_state.json`과 event log에서 마지막 안전 지점부터 재개한다.

### 주기적 총괄 감시

총괄 supervisor는 1분마다 각 run의 heartbeat, queue, 마지막 이벤트, 목표 미달 worker를 확인한다. 실행 가능한 `READY_FOR_WORKER`가 있으면 controller를 자동 재호출하고, 실행할 수 없으면 외부 결과·선행 의존성·등록 worker 중 무엇이 막는지 blocker report로 기록한다. 재수행 가능한 실패는 bounded recovery로 재큐잉하고, 수정 후 실제 worker 재수행과 결과 검증을 기록한다. 오류 해결·재수행·상태 변화가 5분 이상 없을 때만 `supervisor_alert.json`과 채팅 보고로 알린다. worker가 실제로 실행 중이거나 진척이 있으면 보고하지 않는다. supervisor가 설치·실행 중인지 확인되지 않으면 감시 중이라고 보고하지 않는다.

파일·이벤트 감시는 모델 토큰을 사용하지 않는다. 외부 API나 모델 호출은 worker의 승인 게이트를 통과한 경우에만 발생한다. worker·task 완료나 의미 있는 상태 전이는 완료된 작업, artifact, 다음 분석을 보고한다. 무진척, orphan worker, 반복 실패가 발견되면 원인 분석과 재개·대체 경로를 즉시 dispatch하고, 5분 이상 변화가 없을 때만 사용자에게 원인과 다음 행동을 보고한다.

## 비용과 모델 라우팅

결정적 파일 검사, 해시, 정규화, 상태 동기화, polling은 모델을 호출하지 않는다. 간단한 분류와 형식 검사는 저비용 모델 또는 스크립트를 사용한다. identity ambiguity, 충돌하는 증거, mapping anomaly, 최종 후보 선정, 독립 QC 이견에서만 고사양 모델을 권고한다.

각 run에는 `max_cycles`, `max_worker_attempts`, `max_model_calls`, `max_wall_minutes`를 기록한다. 한도에 도달하면 새 작업을 만들지 않고 `BUDGET_STOP`과 재개 조건을 남긴다.

## 검증과 완료 조건

하네스 완료와 domain 결과 완료를 구분한다. 하네스는 상태를 안정적으로 관리해도 domain의 해석과 결론을 대신 검증하지 않는다. 최종 완료에는 해당 adapter가 요구하는 provenance·manifest·독립 QC·완료 검증이 필요하다.

## 운영 방법

run 생성과 domain 작업은 선택한 skill과 adapter 지침을 따른다.

```powershell
python <workspace>\harness\runner.py cycle --profile <domain> --run <run-folder>
```

반복 감시는 운영체제 scheduler 또는 승인된 heartbeat에 연결할 수 있지만, 설치·테스트되기 전에는 백그라운드 감시가 실행 중이라고 주장하지 않는다. `--dry-run`은 외부 작업이나 GUI 조작 없이 상태와 dispatch 계획만 검증한다.

## 스킬 스택 감사와 평가

`harness/SKILL_STACK_AUDIT.md`는 Skill·plugin·script의 책임 중복과 실제 설치·검증 상태를 관리한다. `harness/SKILL_EVALUATION.md`는 dry-run, 오류 주입, provenance, 과학 QC, 비용 회귀를 승격 기준으로 삼는다. 공개 프로젝트의 구현 방식은 참고할 수 있지만, domain 실행 소유자를 바꾸려면 반드시 adapter와 회귀 검증을 추가한다.

## 문서 우선순위

이 파일과 `HARNESS_GUIDE.md`, `harness/EVALUATION_AND_IMPROVEMENT.md`는 범용 실행·평가 지침이다. 날짜나 평가 목적을 가진 문서는 실행 지시가 아니라 평가 기록으로 읽는다. 실제 작업에서는 선택한 domain adapter와 worker 계약을 추가 적용한다.



## Review package at project root

For every research or analysis project, the controller creates a collaborator review package directly under the project root. The package keeps five boundaries: 01_raw, 02_calculated, 03_external_analysis, 04_visual_qc, and 05_figures_reports. Raw inputs and collected provider results are never mixed with derived calculations. The package README lists every folder and file and records input -> analysis -> output filename and extension. Invalid, identity-mismatched, or discarded files are excluded.

Review package README files must present the inventory as a table whenever possible. The minimum columns are: folder, file, input/source, analysis or transformation, output extension, and review purpose.

A review package is review-complete only when its metadata records tool versions, provider/database release, parameters, execution dates, input/output hashes, and script revision. If any item is missing, label the package REVIEW_ONLY and do not claim publication-ready reproducibility.
