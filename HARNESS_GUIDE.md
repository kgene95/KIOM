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
10. 분야별 adapter
11. 진행 보고와 중단 방지

## 목적과 범위

하네스는 AI가 목표를 계획하고 실행하고 검증하고 복구하도록 만드는 제어 계층이다. NP, docking, MD, 문헌, 논문, 웹앱은 분야별 adapter로 연결하고, 실행·기억·검증·승인 규칙은 공통으로 사용한다.

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

`INTAKE → CONTEXT_CHECK → QUESTIONS → PLANNED → WORKTREE_READY → RUNNING → TESTING → VERIFYING → REVIEW_REQUIRED → COMMITTED → MERGED → COMPLETE`를 기본 흐름으로 사용한다. 사용자 승인이나 외부 결과가 필요하면 `WAITING_USER` 또는 `WAITING_EXTERNAL`, 오류는 `FAILED_RETRYABLE`, `BLOCKED`, `INVALIDATED`, `BUDGET_STOP`으로 기록한다.

## 질문·계획·트리거

작업 시작 시 프로젝트 상태, 결정 기록, checkpoint, 이전 승인과 현재 요청을 먼저 읽는다. 이미 답이 있으면 다시 묻지 않는다. 목표가 모호하거나 되돌릴 수 없는 외부 작업·삭제·배포·최종 과학 판단이 필요할 때만 질문한다.

Skill trigger는 사용자 요청과 adapter의 작업 유형으로 결정한다. 서브에이전트 trigger는 독립 파일·리소스·검증 경계를 가진 task가 둘 이상일 때만 사용한다. 단순 작업은 결정적 스크립트로 처리한다.

## workflow와 worktree

계획 문서와 `workflow.json`을 먼저 만들고, 구현은 승인된 branch/worktree에서 한다. worktree 생성 후 baseline test를 실행한다. 기준 branch에 직접 작업하지 않는다. worktree를 만들 수 없으면 상태에 이유를 기록하고 명시적으로 안전한 대체 방식을 선택한다.

## 병렬 실행

의존성이 없고 파일·GUI·계정·provider를 공유하지 않는 task는 같은 dispatch group으로 실행한다. 공유 resource가 있으면 lock을 사용해 직렬화한다. 병렬 worker의 결과는 독립 artifact로 저장하고 총괄이 검증 후 통합한다.

## 테스트·검증·복구

버그는 `재현 → 실패 테스트 → 최소 수정 → 통과 → 전체 회귀 테스트` 순서를 따른다. 완료는 worker의 말이 아니라 테스트 출력, artifact 존재, SHA, provenance, reviewer verdict, Git 상태로 판정한다. 오류는 원인과 재개 조건을 기록하고 bounded retry만 수행한다.

## Git·GitHub 완료 절차

`plan → worktree → implement → test → verify → commit → review → merge → merge 후 재검증 → changelog/state 갱신` 순서다. commit과 merge는 별도 상태다. 외부 전송·삭제·배포·논문 최종화는 승인 게이트를 거친다.

## 상태와 기억

공통 상태는 `PROJECT_STATE.md`, 결정은 `DECISIONS.md`, 실행은 `logs/execution.jsonl`, handoff는 manifest로 저장한다. 대화 기억만으로 재개하지 않는다. 건강한 장기 작업 중에는 조용히 polling하고 완료·실패·중단·사용자 행동 필요 때만 알린다.

## 분야별 adapter

adapter는 task 목록, 입력·출력 계약, 분야별 검증, 외부 connector와 완료 조건만 제공한다. 범용 lifecycle을 복사하지 않는다. 현재 NP는 `harness/NP_ADAPTER.md`와 `skills/run-network-pharmacology/`를 사용한다.

## 진행 보고와 중단 방지

채팅 보고와 상태 전이는 [PROGRESS_REPORTING.md](PROGRESS_REPORTING.md)를 따른다. 총괄은 run 생성, worker 시작·완료, 승인·외부 대기, 오류·재시도·QC, 완료·예산 중지 시 한국어로 현재 상태와 다음 행동을 보고한다. 한 task가 막혀도 독립 task를 계속 실행하며, 필수 task가 막힌 경우에만 최종 gate를 보류한다.
