from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

TERMINAL = {"DONE", "BLOCKED", "FAILED", "WAITING_USER", "WAITING_EXTERNAL", "BUDGET_STOP"}
APPROVAL_TASKS = {"source_reuse_decision", "sea_submission", "pharmmapper_submission"}
EXTERNAL_TASKS = {"sea_collect", "pharmmapper_collect"}

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def write_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)

def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def task_map(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {task["id"]: task for task in queue.get("tasks", [])}

def ready_tasks(queue: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = task_map(queue)
    ready = []
    for task in queue.get("tasks", []):
        if task.get("status") not in {"QUEUED", "READY_FOR_WORKER"}:
            continue
        deps = [tasks[name] for name in task.get("requires", []) if name in tasks]
        if all(dep.get("status") == "DONE" for dep in deps):
            ready.append(task)
    return ready

def conflict_key(task: dict[str, Any]) -> str:
    if task["id"] in {"sea_submission", "sea_collect"}:
        return "SEA"
    if task["id"] in {"pharmmapper_submission", "pharmmapper_collect"}:
        return "PharmMapper"
    if task["id"] in {"final_ppi", "independent_qc", "manuscript_review"}:
        return "final-branch"
    return task.get("agent", "unknown")

def build_plan(queue: dict[str, Any], cycle: int) -> dict[str, Any]:
    by_resource: dict[str, list[dict[str, Any]]] = {}
    for task in ready_tasks(queue):
        by_resource.setdefault(conflict_key(task), []).append(task)
    groups = [[{"id": t["id"], "agent": t.get("agent"), "resource": resource} for t in tasks]
              for resource, tasks in by_resource.items()]
    return {"cycle": cycle, "created_at_utc": now(), "parallel_groups": groups,
            "ready_count": sum(len(group) for group in groups), "queue_digest": digest(queue),
            "policy": "parallel only across independent resource groups; single controller per resource"}

def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at_utc": now(), **event}, ensure_ascii=False) + "\n")

def validate_run(run: Path) -> dict[str, Any]:
    """NP 최종 게이트를 판정한다. 외부 provider를 호출하지 않는다."""
    request = read(run / "request.json", {})
    queue = read(run / "work_queue.json", {"tasks": []})
    tasks = task_map(queue)
    missing_input = [key for key in ("compound_input", "disease_input", "species") if not request.get(key)]
    terminal_required = ["independent_qc", "manuscript_review"]
    unfinished = [key for key in terminal_required if tasks.get(key, {}).get("status") != "DONE"]
    waiting = [{"id": task.get("id"), "status": task.get("status"),
                "detail": task.get("detail") or task.get("next_action")}
               for task in queue.get("tasks", [])
               if str(task.get("status", "")).startswith("WAITING")]
    if missing_input:
        status, next_action = "BLOCKED_NEEDS_USER", "필수 입력을 기록한 뒤 재실행"
    elif waiting:
        status, next_action = "WAITING", "대기 항목을 해결하거나 연결된 provider 상태를 확인"
    elif unfinished:
        status, next_action = "IN_PROGRESS", "미완료 task의 등록 worker를 dispatch"
    else:
        status, next_action = "PASS", "완료 manifest와 Git 상태를 확인"
    result = {"status": status, "missing_input": missing_input,
              "unfinished": unfinished, "waiting": waiting, "next_action": next_action}
    write_atomic(run / "np_validation.json", result)
    append_event(run / "event_log.jsonl", {"event": "np_validation", "status": status})
    return result

def cycle(run: Path, dry_run: bool = False, max_cycles: int = 1) -> dict[str, Any]:
    queue_path = run / "work_queue.json"
    queue = read(queue_path, {"tasks": []})
    state_path = run / "harness_state.json"
    state = read(state_path, {"run_id": read(run / "request.json", {}).get("run_id", run.name),
                              "cycle": 0, "max_cycles": max_cycles, "max_worker_attempts": 3,
                              "max_model_calls": 12, "model_calls": 0, "status": "RUNNING"})
    state["cycle"] = int(state.get("cycle", 0)) + 1
    state["max_cycles"] = max_cycles
    if state["cycle"] > max_cycles:
        state.update({"status": "BUDGET_STOP", "next_action": "increase max_cycles or resume explicitly"})
        write_atomic(state_path, state)
        append_event(run / "event_log.jsonl", {"event": "budget_stop", "reason": "max_cycles"})
        return state

    if not dry_run:
        scripts = Path(__file__).parents[1] / "skills" / "run-network-pharmacology" / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        try:
            import np_agent_queue
            np_agent_queue.collect(run)
            queue = read(queue_path, queue)
        except Exception as exc:
            state.update({"status": "FAILED", "last_error": repr(exc), "next_action": "repair queue sync and rerun"})
            write_atomic(state_path, state)
            append_event(run / "event_log.jsonl", {"event": "sync_failed", "error": repr(exc)})
            return state

    plan = build_plan(queue, state["cycle"])
    write_atomic(run / "dispatch_plan.json", plan)
    for task in ready_tasks(queue):
        if task["id"] in APPROVAL_TASKS:
            task.update({"status": "WAITING_USER", "next_action": "record explicit approval in the run manifest"})
        elif task["id"] in EXTERNAL_TASKS:
            task.update({"status": "WAITING_EXTERNAL", "next_action": "check official job status or connected Gmail connector"})
        else:
            task.update({"status": "READY_FOR_WORKER", "next_action": "dispatch registered worker and verify its artifact contract"})
    if not dry_run:
        write_atomic(queue_path, queue)
    state.update({"status": "WAITING" if any(t.get("status", "").startswith("WAITING") for t in queue.get("tasks", [])) else "READY",
                  "last_updated_utc": now(), "next_action": "execute dispatch_plan.json; do not wait without a scheduled cycle",
                  "ready_count": plan["ready_count"]})
    write_atomic(state_path, state)
    append_event(run / "event_log.jsonl", {"event": "cycle_complete", "cycle": state["cycle"], "dry_run": dry_run, "ready_count": plan["ready_count"]})
    return state

def main() -> None:
    parser = argparse.ArgumentParser(description="Durable NP orchestration harness")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("cycle")
    command.add_argument("--run", required=True)
    command.add_argument("--dry-run", action="store_true")
    command.add_argument("--max-cycles", type=int, default=1)
    validate = sub.add_parser("validate")
    validate.add_argument("--run", required=True)
    args = parser.parse_args()
    result = validate_run(Path(args.run)) if args.command == "validate" else cycle(Path(args.run), dry_run=args.dry_run, max_cycles=args.max_cycles)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
