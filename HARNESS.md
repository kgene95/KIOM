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

이 하네스는 NP, docking, MD, 문헌, 논문, 웹앱 등 여러 분야에 공통으로 적용되는 실행 제어 계층이다. 작업이 자료 도착이나 외부 job 완료에서 멈추지 않도록 상태, 의존성, 승인, 재시도, 재시작 조건, 비용 한도를 저장한다. 과학적 해석과 최종 결론은 분야별 adapter와 독립 QC가 담당한다.

## 설계 원칙

- 저장소 안의 Markdown, JSON schema, 실행 로그와 결과 manifest를 에이전트가 읽을 수 있는 단일 기준으로 사용한다.
- 상태 표시와 실제 실행을 분리한다. `READY_FOR_WORKER`는 실행 대기이며 `DONE`이 아니다.
- 독립 작업은 병렬 그룹으로 계획하되 같은 파일·GUI·외부 계정은 단일 컨트롤러만 조작한다.
- 외부 제출, Gmail 접근, CAPTCHA, 로그인, 기존 자료 재사용, 최종 과학 판단은 승인 게이트로 명시한다.
- 자동 재시도는 일시 오류에만 제한하고, 같은 실패를 무한 반복하지 않는다.
- 모든 사이클은 원자적으로 상태를 저장하고, 중단 뒤 같은 run을 재개할 수 있어야 한다.
- 완료는 경과 시간이 아니라 산출물·검증 로그·독립 QC로 판정한다.

## 실행 구조

`harness/runner.py`가 범용 진입점이고, 분야별 adapter가 task 정의와 산출물 검증을 제공한다. 현재 NP adapter는 `harness/np_harness.py`와 `harness/NP_ADAPTER.md`다. 한 사이클은 다음 순서로 동작한다.

1. run 잠금과 `harness_state.json` 복구
2. 기존 NP 큐와 외부 결과 manifest 동기화
3. 이벤트 기록 및 변경 입력 감지
4. 의존성이 충족된 작업의 병렬 dispatch 계획 작성
5. 승인 필요·외부 대기·실행 가능 작업 분리
6. bounded retry와 예산 확인
7. 실행 결과와 다음 재개 조건 원자 저장
8. 완료·실패·필수 사용자 행동만 알림 대상으로 등록

현재 단계의 하네스는 안전한 상태 조정과 dispatch 계획을 먼저 보장한다. 실제 SEA/PharmMapper 제출과 Gmail 읽기는 연결된 커넥터와 별도 승인 후 worker adapter를 통해서만 실행한다.

등록된 worker의 입력·출력·실패 계약은 `harness/WORKER_CONTRACT.md`와 `harness/worker_registry.json`에 있다. registry에 없는 임의 명령은 실행하지 않는다.

## 총괄과 분야별 세부 에이전트

| 역할 | 책임 | 입력 | 산출물 |
|---|---|---|---|
| Agent 0 총괄 | 목표, DAG, 승인, 재시작, 비용, 알림 | 사용자 목표와 run 상태 | 실행 상태, dispatch 계획, 다음 행동 |
| 분야 총괄 | 목표, DAG, 승인, 재시작, 비용, 알림 | 사용자 목표와 run 상태 | 실행 상태, dispatch 계획, 다음 행동 |
| 분야 worker | 해당 분야의 입력·계산·외부 연결 | adapter 계약 | 검증된 artifact와 handoff |
| 독립 검증 worker | lineage, 입력 변경 영향, 재실행 판정 | 모든 새 산출물 | PASS, CORRECT_AND_RERUN, BLOCKED |

역할 이름만 적고 실행된 것으로 간주하지 않는다. 각 역할은 검증 가능한 파일과 상태 전이를 남겨야 한다.

## 이벤트와 병렬 실행

입력 검증, 외부 job ID 생성, 결과 raw 파일 도착, Gmail 완료 알림, QC 수정, 사용자 승인과 파일 변경은 모두 이벤트다. 이벤트가 발생하면 총괄은 영향을 받는 작업을 다시 계산한다.

- 구조 QC와 질환 표적 수집은 서로 독립이면 병렬 실행한다.
- SEA와 PharmMapper 제출·상태 확인은 각 job의 격리된 작업으로 병렬 실행할 수 있다.
- 보조 provider가 지연되어도 검증된 primary branch의 독립 분석은 계속한다.
- 새 raw 입력이 오면 영향받은 downstream만 `INVALIDATED` 후 QC를 거쳐 재실행한다.
- 같은 run의 동일 외부 계정, GUI, 파일 묶음은 병렬 작업이 동시에 조작하지 않는다.

`dispatch_plan.json`에는 cycle, 병렬 그룹, 의존성, 파일 충돌 방지 정보가 남는다.

## 승인·외부 서비스·알림

다음은 자동 실행하지 않고 `WAITING_USER` 또는 `WAITING_EXTERNAL`로 저장한다.

- 기존 자료 재사용 또는 새 source job 제출
- 연락 이메일 사용, 로그인, CAPTCHA, 이용약관 동의
- raw 연구자료의 외부 전송
- 논문용 최종 결론, docking 후보 확정, 결과 branch 병합

Gmail은 실제로 연결되고 테스트된 connector/heartbeat가 있을 때만 감시한다. 메일 본문·주소·토큰은 저장하지 않고 provider와 job ID로만 결과를 대응한다. 알림은 완료, 실패, 예기치 않은 중단, 사용자 행동 필요 시에만 생성한다.

## 실패 복구와 재시작

각 작업은 `attempts`, `max_attempts`, `last_error`, `resume_condition`, `next_action`, `last_updated_utc`를 가진다.

- 네트워크·일시 오류: 제한된 재시도 후 문서화된 대체 경로를 시도한다.
- 입력/QC 오류: 원인을 고친 뒤 영향받은 하류만 invalidation하고 재실행한다.
- 승인·인증·CAPTCHA: 자동 반복하지 않고 정확한 재개 조건을 저장한다.
- 같은 오류가 예산을 넘으면 `BLOCKED`로 종료하고 사용자에게 원인과 필요한 행동을 알린다.
- 프로세스가 끊겨도 `harness_state.json`과 event log에서 마지막 안전 지점부터 재개한다.

## 비용과 모델 라우팅

결정적 파일 검사, 해시, 정규화, 상태 동기화, polling은 모델을 호출하지 않는다. 간단한 분류와 형식 검사는 저비용 모델 또는 스크립트를 사용한다. identity ambiguity, 충돌하는 증거, mapping anomaly, 최종 후보 선정, 독립 QC 이견에서만 고사양 모델을 권고한다.

각 run에는 `max_cycles`, `max_worker_attempts`, `max_model_calls`, `max_wall_minutes`를 기록한다. 한도에 도달하면 새 작업을 만들지 않고 `BUDGET_STOP`과 재개 조건을 남긴다.

## 검증과 완료 조건

하네스 완료와 NP 완료를 구분한다. 하네스는 상태를 안정적으로 관리해도 NP 과학 결과를 대신 검증하지 않는다. 최종 완료에는 기존 `validate_np_completion.py`, `privacy_audit.py`, 독립 Agent 4 PASS, provenance/manifest, 명확한 `DOCKING_NOT_STARTED`가 필요하다.

## 운영 방법

run 생성과 과학 분석은 선택한 domain skill 지침을 따른다. NP adapter를 한 번 동기화하려면 다음처럼 실행한다.

```powershell
python D:\GPT-CODECX\KIOM\harness\runner.py cycle --profile np --run D:\GPT-CODECX\KIOM_NP_Projects\NP_Runs\runs\<RUN_ID>
```

반복 감시는 Windows Task Scheduler 또는 승인된 heartbeat에 연결할 수 있지만, scheduler가 설치·테스트되기 전에는 백그라운드 감시가 실행 중이라고 주장하지 않는다. 설치 초안은 `harness/install_np_watchdog.ps1`에 있으며 명시적 검토 전에는 설치하지 않는다. `--dry-run`은 외부 제출이나 GUI 조작 없이 상태와 dispatch 계획만 검증한다.

## 스킬 스택 감사와 평가

`harness/SKILL_STACK_AUDIT.md`는 Skill·plugin·script의 책임 중복과 실제 설치·검증 상태를 관리한다. `harness/SKILL_EVALUATION.md`는 dry-run, 오류 주입, provenance, 과학 QC, 비용 회귀를 승격 기준으로 삼는다. 공개 프로젝트의 구현 방식은 참고할 수 있지만, domain 실행 소유자를 바꾸려면 반드시 adapter와 회귀 검증을 추가한다.
