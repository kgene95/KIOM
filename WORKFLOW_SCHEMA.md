# Workflow schema

## 필수 필드

`workflow_id`, `goal`, `success_criteria`, `tasks`, `dependencies`, `resources`, `approval_policy`, `budget`, `state`, `checkpoint`, `next_action`, `created_at_utc`, `updated_at_utc`.

## Task 필드

`task_id`, `owner`, `kind`, `requires`, `resource_locks`, `input_paths`, `output_contract`, `status`, `attempts`, `max_attempts`, `last_error`, `resume_condition`.

## 상태 규칙

`DONE`은 output contract와 verification evidence가 모두 있을 때만 허용한다. 입력 hash가 바뀌면 영향받은 downstream을 `INVALIDATED`한다. `WAITING_USER`와 `WAITING_EXTERNAL`은 실패가 아니며 정확한 재개 조건을 가져야 한다.
