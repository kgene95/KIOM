"""Durable NP worker dispatcher.

The queue is the handoff contract.  This module is intentionally small: it
does not invent work, bypass provider approvals, or hide exceptions.  It
dispatches only registered local callables and records every boundary event.
"""
from __future__ import annotations

import importlib
import time
import datetime as dt
import json
import os
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

from np_harness import append_event, read, ready_tasks, write_atomic, validate_queue_contract, transition_task

Worker = Callable[[Path], dict[str, Any]]

TASK_WORKERS = {
    "external_data_intake": "external_data_intake",
    "identity": "compound_identity",
    "disease_targets": "disease_target_collection",
    "structure_handoff": "structure_qc",
    "sea_collect": "sea_collect",
    "pharmmapper_collect": "pharmmapper_collect",
    "initial_ppi": "initial_ppi",
    "overlap_analysis": "overlap_analysis",
    "ppi_analysis": "ppi_analysis",
    "enrichment_analysis": "enrichment_analysis",
    "integration_analysis": "integration_analysis",
    "final_ppi": "integration_analysis",
    "independent_qc": "independent_qc",
    "manuscript_review": "manuscript_review",
    "cytoscape_visualization": "cytoscape_visualization",
    "docking_candidate_selection": "docking_candidate_selection",
    "figure_draft": "figure_draft",
    "methods_results_draft": "methods_results_draft",
    "completion_packager": "completion_packager",
}
REGISTRY_PATH = Path(__file__).with_name("worker_registry.json")

class ControllerBusy(RuntimeError):
    pass

def recover_orphans(run: Path, queue: dict[str, Any]) -> dict[str, Any]:
    """Move expired RUNNING tasks back to bounded retry instead of idling forever."""
    now = dt.datetime.now(dt.timezone.utc)
    for task in queue.get("tasks", []):
        if task.get("status") != "RUNNING":
            continue
        try:
            lease_until = dt.datetime.fromisoformat(task.get("lease_until", ""))
        except ValueError:
            lease_until = now
        if lease_until <= now:
            transition_task(task, "RETRY_WAIT")
            task.update({"detail": "worker lease expired; orphan recovered", "next_attempt_at": now.isoformat()})
            append_event(run / "event_log.jsonl", {"event": "orphan_recovered", "task_id": task.get("id"), "worker_pid": task.get("worker_pid")})
    return queue

@contextmanager
def controller_lease(run: Path, ttl_seconds: int = 90):
    """Acquire one atomic lease per run; stale leases are recoverable."""
    lease_path = run / "controller_lease.json"
    token = uuid.uuid4().hex
    now = dt.datetime.now(dt.timezone.utc)
    if lease_path.exists():
        try:
            old = json.loads(lease_path.read_text(encoding="utf-8-sig"))
            expires = dt.datetime.fromisoformat(old.get("lease_until", ""))
            if expires > now:
                raise ControllerBusy(f"run lease owned by pid {old.get('pid')}")
            lease_path.unlink(missing_ok=True)
        except ControllerBusy:
            raise
        except (OSError, ValueError, json.JSONDecodeError):
            lease_path.unlink(missing_ok=True)
    payload = {"pid": os.getpid(), "token": token, "acquired_utc": now.isoformat(), "lease_until": (now + dt.timedelta(seconds=ttl_seconds)).isoformat()}
    try:
        fd = os.open(str(lease_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    except FileExistsError as exc:
        raise ControllerBusy("run lease acquisition race") from exc
    try:
        yield payload
    finally:
        try:
            current = json.loads(lease_path.read_text(encoding="utf-8-sig"))
            if current.get("token") == token:
                lease_path.unlink(missing_ok=True)
        except (OSError, json.JSONDecodeError):
            pass

def refresh_controller_lease(run: Path, ttl_seconds: int = 180) -> None:
    path = run / "controller_lease.json"
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if int(payload.get("pid", -1)) == os.getpid():
            payload["lease_until"] = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=ttl_seconds)).isoformat()
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError):
        return


def default_workers(registry_path: Path = REGISTRY_PATH) -> dict[str, Worker]:
    registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    # Local workers import provider adapters from the app runtime and optional
    # dependencies from the project runtime bundle.  The controller is often
    # launched directly, so establish these paths here rather than relying on
    # a shell-specific PYTHONPATH.
    sys.path.insert(0, str(registry_path.parents[1] / "apps" / "kiom_np_workbench"))
    sys.path.insert(0, str(registry_path.parents[1] / ".runtime_deps"))
    module = importlib.import_module("np_workers")
    workers = {}
    planned = registry.get("planned_workers", {})
    for task_id, worker_name in TASK_WORKERS.items():
        spec = registry.get("workers", {}).get(worker_name)
        if not spec:
            continue
        status = planned.get(worker_name, {}).get("status", "implemented")
        if status not in {"implemented", "verified"}:
            continue
        function = getattr(module, spec["function"], None)
        if callable(function):
            workers[task_id] = function
    return workers


def dispatch_ready_tasks(
    run: Path,
    queue: dict[str, Any],
    workers: dict[str, Worker] | None = None,
    *,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Run each explicitly ready task and persist a visible outcome."""
    workers = workers or default_workers()
    def alert(task_id: str, severity: str, message: str) -> None:
        write_atomic(run / "controller_alert.json", {
            "run_id": run.name, "task_id": task_id, "severity": severity,
            "message": message, "updated_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        })
    for task in ready_tasks(queue):
        task_id = task["id"]
        worker = workers.get(task_id)
        attempts = int(task.get("attempts", 0)) + 1
        task["attempts"] = attempts
        if worker is None:
            transition_task(task, "FAILED")
            task.update({"detail": "등록된 worker가 없습니다."})
            alert(task_id, "HIGH", "등록된 worker가 없어 총괄 개입이 필요합니다.")
            append_event(run / "event_log.jsonl", {"event": "worker_failed", "task_id": task_id, "reason": "unregistered_worker"})
            continue
        started = dt.datetime.now(dt.timezone.utc)
        transition_task(task, "RUNNING")
        task.update({"started_at_utc": started.isoformat(), "worker_pid": os.getpid(), "lease_until": (started + dt.timedelta(seconds=90)).isoformat()})
        append_event(run / "event_log.jsonl", {"event": "worker_started", "task_id": task_id, "worker_name": getattr(worker, "__name__", task_id), "attempt": attempts})
        try:
            result = worker(run) or {}
            result_status = str(result.get("status", "DONE"))
            outputs = result.get("outputs", [])
            missing_outputs=[]
            for output in outputs:
                path=Path(str(output))
                if not path.is_absolute(): path=run/path
                if not path.is_file(): missing_outputs.append(str(path))
            if result_status == "DONE" and (not outputs or missing_outputs):
                result_status="FAILED"
                result={**result, "reason": "artifact contract failed", "missing_outputs": missing_outputs}
            if result_status == "DONE":
                transition_task(task, "DONE")
                task.update({"info": {"outputs": result.get("outputs", [])}})
                append_event(run / "event_log.jsonl", {"event": "worker_completed", "task_id": task_id, "worker_task_id": result.get("task_id", task_id), "attempt": attempts})
            elif (result_status.startswith("FAILED") or result_status == "RETRY_WAIT" or result_status == "CORRECT_AND_RERUN") and attempts >= max_attempts:
                transition_task(task, "FAILED")
                task.update({"detail": result.get("reason", "worker failed"), "info": result})
                alert(task_id, "HIGH", result.get("reason", "worker failed"))
                append_event(run / "event_log.jsonl", {"event": "worker_failed", "task_id": task_id, "attempt": attempts, "reason": result.get("reason", "worker failed")})
            else:
                next_attempt = started + dt.timedelta(seconds=min(300, 5 * (2 ** max(0, attempts - 1))))
                next_status = "RETRY_WAIT" if result_status in {"FAILED_RETRYABLE", "RETRY_WAIT", "CORRECT_AND_RERUN"} else result_status
                transition_task(task, next_status)
                task.update({"detail": result.get("next_action", "worker returned a waiting state"), "info": result, "next_attempt_at": next_attempt.isoformat() if result_status in {"FAILED_RETRYABLE", "RETRY_WAIT"} else None})
                alert(task_id, "MEDIUM", result.get("next_action", f"worker returned {result_status}"))
                append_event(run / "event_log.jsonl", {"event": "worker_waiting", "task_id": task_id, "worker_task_id": result.get("task_id", task_id), "attempt": attempts, "status": result_status})
        except Exception as exc:  # boundary: never let one worker stop the controller
            status = "FAILED" if attempts >= max_attempts else "RETRY_WAIT"
            next_attempt = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=min(300, 5 * (2 ** max(0, attempts - 1))))
            transition_task(task, status)
            task.update({"detail": repr(exc), "next_attempt_at": None if status == "FAILED" else next_attempt.isoformat()})
            alert(task_id, "HIGH" if status == "FAILED" else "MEDIUM", repr(exc))
            append_event(run / "event_log.jsonl", {"event": "worker_failed", "task_id": task_id, "attempt": attempts, "reason": repr(exc), "retryable": status != "FAILED"})
    return queue


def run_controller(run: Path, *, max_cycles: int = 1, _lease_held: bool = False) -> dict[str, Any]:
    """Run bounded reconciliation/dispatch cycles for one run."""
    from np_harness import cycle, reconcile_queue

    lease = None
    if not _lease_held:
      try:
          lease = controller_lease(run)
          lease.__enter__()
      except ControllerBusy as exc:
          append_event(run / "event_log.jsonl", {"event": "duplicate_controller", "reason": str(exc)})
          return {"status": "CONTROLLER_BUSY", "next_action": "existing controller lease remains active", "last_error": str(exc)}
    state: dict[str, Any] = {}
    try:
      for _ in range(max_cycles):
        prior = read(run / "harness_state.json", {})
        # max_cycles is a per-tick safety budget; persisted cycle numbers are
        # monotonic for audit but must not permanently disable future ticks.
        current_cycle = int(prior.get("cycle", 0))
        state = cycle(run, dry_run=False, max_cycles=current_cycle + max_cycles)
        queue_path = run / "work_queue.json"
        queue = read(queue_path, {"tasks": []})
        contract_errors = validate_queue_contract(queue)
        if contract_errors:
            message = "; ".join(contract_errors[:8])
            write_atomic(run / "controller_alert.json", {"run_id": run.name, "severity": "HIGH", "message": "queue contract invalid: " + message, "updated_utc": dt.datetime.now(dt.timezone.utc).isoformat()})
            append_event(run / "event_log.jsonl", {"event": "state_contract_error", "errors": contract_errors})
            state.update({"status": "BLOCKED", "last_error": message, "next_action": "repair work_queue.json contract"})
            write_atomic(run / "harness_state.json", state)
            return state
        queue = recover_orphans(run, queue)
        expected_cid = str(read(run / "structure_manifest.json", {}).get("cid") or "") or None
        queue = reconcile_queue(run, queue, expected_cid=expected_cid)
        queue = dispatch_ready_tasks(run, queue)
        write_atomic(queue_path, queue)
        # Return the post-dispatch state, not the pre-dispatch cycle state.
        # Otherwise the heartbeat can claim READY while a worker is waiting
        # for an explicit external/QC gate.
        waiting = any(str(task.get("status", "")).startswith("WAITING") for task in queue.get("tasks", []))
        active = any(task.get("status") in {"READY_FOR_WORKER", "RUNNING", "RETRY_WAIT"} for task in queue.get("tasks", []))
        failed = [task for task in queue.get("tasks", []) if task.get("status") == "FAILED"]
        required = {"independent_qc", "manuscript_review", "cytoscape_visualization", "docking_candidate_selection", "methods_results_draft", "completion_packager"}
        task_map_current = {task.get("id"): task for task in queue.get("tasks", [])}
        complete = required.issubset(task_map_current) and all(task_map_current[name].get("status") == "DONE" for name in required)
        status = "FAILED" if failed else ("COMPLETE" if complete else ("WAITING" if waiting else ("READY" if active else "IDLE")))
        state.update({"status": status, "ready_count": sum(1 for task in queue.get("tasks", []) if task.get("status") in {"READY_FOR_WORKER", "RUNNING", "RETRY_WAIT"}), "last_updated_utc": dt.datetime.now(dt.timezone.utc).isoformat()})
        if complete:
            state.update({"next_action": "과학적 결과 검토 후 별도 도킹 workflow handoff", "completion_event": "NP_ANALYSIS_COMPLETE"})
        if failed:
            state.update({"last_error": "; ".join(f"{task.get('id')}: {task.get('detail', 'worker failed')}" for task in failed), "next_action": "controller_alert.json 확인 후 실패 원인 보정 및 재실행"})
        write_atomic(run / "harness_state.json", state)
        if not any(task.get("status") in {"READY_FOR_WORKER", "RUNNING", "RETRY_WAIT"} for task in queue.get("tasks", [])):
            break
      return state
    finally:
      if lease is not None:
        lease.__exit__(None, None, None)


def loop_controller(runs: list[Path], *, interval_seconds: int = 30, max_cycles_per_tick: int = 10) -> None:
    """Keep reconciling and dispatching runs without consuming model tokens."""
    leases=[]
    active=[]
    for run in runs:
        try:
            lease=controller_lease(run, ttl_seconds=max(180, interval_seconds * 4))
            lease.__enter__(); leases.append((run, lease)); active.append(run)
        except ControllerBusy as exc:
            append_event(run / "event_log.jsonl", {"event": "duplicate_controller", "reason": str(exc)})
    try:
        while True:
            for run in active:
                heartbeat = run / "controller_heartbeat.json"
                payload = {"run_id": run.name, "pid": __import__("os").getpid(),
                           "updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "status": "RUNNING"}
                try:
                    refresh_controller_lease(run, ttl_seconds=max(180, interval_seconds * 4))
                    state = run_controller(run, max_cycles=max_cycles_per_tick, _lease_held=True)
                    payload.update({"controller_status": state.get("status"), "run_status": state.get("status"), "next_action": state.get("next_action"), "last_error": state.get("last_error")})
                except Exception as exc:  # watchdog boundary: record and continue with other runs
                    payload.update({"controller_status": "FAILED_RETRYABLE", "last_error": repr(exc)})
                    append_event(run / "event_log.jsonl", {"event": "controller_failed", "reason": repr(exc)})
                write_atomic(heartbeat, payload)
            time.sleep(max(1, interval_seconds))
    finally:
        for run, lease in leases:
            lease.__exit__(None, None, None)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Bounded durable NP controller")
    parser.add_argument("--run", required=True)
    parser.add_argument("--max-cycles", type=int, default=1)
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval-seconds", type=int, default=30)
    args = parser.parse_args()
    if args.loop:
        loop_controller([Path(args.run)], interval_seconds=args.interval_seconds, max_cycles_per_tick=args.max_cycles)
    else:
        print(json.dumps(run_controller(Path(args.run), max_cycles=args.max_cycles), ensure_ascii=False, indent=2))
