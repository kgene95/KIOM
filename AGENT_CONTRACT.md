# 범용 에이전트 계약

## 목차

1. Controller
2. Planner
3. Worker
4. Reviewer
5. Verifier
6. Notifier
7. 질문과 handoff
8. 진행 보고
9. 사전 점검

## Controller

목표, 상태, 승인, 예산, dispatch, 재시작을 관리한다. 독립 task는 병렬화하고, 완료를 추정하지 않는다.

## Planner

요구사항과 성공 기준을 `requirements.md`, `plan.md`, `acceptance-criteria.md`로 고정한다. 누락·충돌을 식별하고 질문이 필요한 경우만 질문한다.

## Worker

등록된 책임 하나만 수행한다. 입력 hash, 출력 경로, 도구 버전, 시각, 오류, 다음 행동을 기록한다. 다른 worker의 파일을 임의로 수정하지 않는다.

## Reviewer

계획과 변경이 일치하는지 검토한다. 중요한 문제는 수정 전에 분류하고, 사소한 개선은 deferred로 기록한다.

## Verifier

테스트·artifact·SHA·provenance·Git 상태를 독립 확인한다. verdict는 `PASS`, `CORRECT_AND_RERUN`, `BLOCKED_NEEDS_USER` 중 하나다.

## Notifier

완료, 실패, 예기치 않은 중단, 사용자 행동 필요 시에만 알린다. 건강한 polling이나 반복 상태를 매번 통지하지 않는다.

## 질문과 handoff

질문 전 `PROJECT_STATE.md`, `DECISIONS.md`, 승인 기록과 checkpoint를 검색한다. handoff는 채팅이 아니라 `run_id`, `task_id`, parent/child, 입력·출력 hash, branch, 검증 상태, next action을 가진 manifest다.

## 진행 보고

총괄은 의미 있는 상태 변화마다 한국어 채팅 보고를 남긴다. worker 하나의 실패·외부 대기·승인 대기가 전체 workflow 종료 사유가 되지 않도록 독립 task를 계속 dispatch하고, 재개 조건과 다음 행동을 기록한다. 변화 없는 polling은 반복 보고하지 않는다.

## 사전 점검

Planner와 Controller는 실행 전 전체 workflow와 의존성을 파악하고 필요한 Skill, plugin, connector, 로컬 프로그램, 이메일·권한·승인을 조사한다. 사용자가 직접 처리해야 할 항목은 최우선순위 목록으로 한 번에 고지하고, 준비가 끝난 항목은 다시 묻지 않는다. `PREFLIGHT_READY` 전에는 장시간 worker를 시작하지 않는다.
