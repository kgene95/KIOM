# Agent Execution Log

모든 worker와 총괄은 `event_log.jsonl`에 한 줄의 구조화 레코드를 남긴다.

필수 필드:

```json
{
  "at_utc": "2026-10-10T00:00:00+00:00",
  "run_id": "...",
  "cycle": 1,
  "task_id": "disease_targets",
  "agent": "agent1",
  "event": "started|completed|failed|waiting|invalidated|resumed",
  "input_sha256": ["..."],
  "output_paths": ["..."],
  "output_sha256": ["..."],
  "attempt": 1,
  "model": "deterministic|low|standard|high",
  "tool_calls": 0,
  "error_class": null,
  "next_action": "...",
  "resume_condition": "..."
}
```

로그는 사람이 읽는 진행 문장을 대신하지 않는다. 로그는 재시작·감사·비용 분석의 기계 기준이며, mail 본문·토큰·비밀번호는 기록하지 않는다.
