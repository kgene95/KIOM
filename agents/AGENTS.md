# KIOM NP 에이전트 운영 규칙

이 파일은 범용 계약을 적용한 NP domain adapter다. 모든 분야에 공통인 총괄·worker·검증자 규칙은 [GENERIC_AGENTS.md](GENERIC_AGENTS.md)에 있고, NP-specific task mapping은 [../harness/NP_ADAPTER.md](../harness/NP_ADAPTER.md)에 있다.

## 목차

1. 공통 실행 계약
2. 총괄 Agent 0
3. Agent 1: 구조·자료
4. Agent 2: 외부 수집
5. Agent 3: 네트워크·경로
6. Agent 4: 독립 QC
7. Agent 5: 원고 근거
8. 에이전트 간 handoff
9. 금지 사항

## 공통 실행 계약

모든 작업은 `입력 계약 → 실행 → 검증 → 산출물 → 다음 이벤트`를 남긴다. 상태가 `DONE`인 작업은 필수 산출물과 검증 근거가 있는 경우에만 인정한다. 실패 시 원인, 시도 횟수, 다음 행동, 재개 조건을 기록한다. 대화가 끊겨도 run 폴더만으로 재개할 수 있어야 한다.

모든 에이전트는 한국어로 사용자-facing 상태를 작성하고, raw 파일·주소·비밀번호·토큰·메일 본문을 공유 산출물에 넣지 않는다.

## Cross-device 공통 규칙

이 파일은 로컬 PC, Codex, ChatGPT Work, GitHub checkout 사이에서 동일한 작업 계약으로 취급한다. 환경이 바뀌면 `research-project-memory`의 `AI_CONTEXT.md`, `PROJECT_STATE.md`, `DECISIONS.md`, `HANDOFF.md`를 먼저 읽고, 숨은 대화 기억을 근거로 삼지 않는다. GitHub의 skills/scripts와 OneDrive의 raw 파일은 각각의 canonical 위치와 SHA를 기록한다. 환경별 실행기 차이는 `environment`, `connector_status`, `verification_status`로 명시한다.

## 총괄 Agent 0

총괄은 직접 모든 과학 계산을 독점하지 않는다. 목표와 승인 범위를 고정하고, `harness_state.json`, `dispatch_plan.json`, `event_log.jsonl`, `execution_state.json`을 관리한다. 새 manifest나 결과가 생기면 영향을 받는 downstream을 계산해 즉시 실행 계획을 갱신한다. 단순 대기 상태를 완료로 보고하지 않는다.

## Agent 1: 구조·자료

CID, isomeric SMILES, InChIKey, 구조 파일 SHA, 질환 ontology와 stable ID를 검증한다. 원본과 정규화 파일을 분리하고 `structure_manifest.json`, `disease_target_manifest.json`, `handoff_to_agent2.json`을 남긴다. 구조가 검증되면 질환 수집을 기다리지 않고 Agent 2 준비 작업을 깨운다.

## Agent 2: 외부 수집

검증된 handoff와 명시적 승인이 없으면 제출하지 않는다. job ID, input SHA, result URL과 raw SHA를 대응시키며, 결과 수신 시 즉시 원본 보존·검증·downstream unblock을 요청한다. Gmail 확인은 연결된 connector가 실제로 동작할 때만 수행한다.

## Agent 3: 네트워크·경로

검증된 입력만 사용한다. 질환 자료나 외부 provider 하나가 지연되어도 독립적으로 검증 가능한 branch는 병렬 실행한다. STRING functional PPI와 OmniPath overlay, topology, enrichment를 구분하고 결과마다 branch와 입력 hash를 기록한다.

## Agent 4: 독립 QC

Agent 3 결과를 그대로 승인하지 않는다. identity, species, mapping, provenance, input hash, source-native score와 결과 재현성을 검사한다. verdict는 `PASS`, `CORRECT_AND_RERUN`, `BLOCKED_NEEDS_USER` 중 하나로 기록한다.

## Agent 5: 원고 근거

frozen output과 검토된 문헌만 사용한다. Agent 4 PASS 전에는 최종 Methods/Results나 figure legend를 확정하지 않는다. 주장마다 근거와 한계를 연결한다.

## 에이전트 간 handoff

Handoff는 채팅 메시지가 아니라 run 폴더의 검증 가능한 manifest다. 최소 필드는 `run_id`, `task_id`, `parent_task_ids`, `input_paths`, `input_sha256`, `output_paths`, `output_sha256`, `species`, `branch`, `created_at_utc`, `verification_status`, `next_action`이다. 파일이 바뀌면 하류 결과를 자동으로 `INVALIDATED`한다.

## 금지 사항

- 메일이 올 것이라고 가정하고 무기한 대기하지 않는다.
- 같은 실패를 무한 재시도하지 않는다.
- 파일명만으로 기존 자료를 검증하거나 job을 화합물에 임의 배정하지 않는다.
- 검증되지 않은 자료를 primary branch에 섞지 않는다.
- 병렬 에이전트가 같은 파일, GUI, 외부 계정을 동시에 조작하지 않는다.
- 실제 실행·검증 없이 완료를 선언하지 않는다.
