from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import urllib.request
import os
import sys
import time
from pathlib import Path
from typing import Any

TERMINAL = {"DONE", "BLOCKED", "FAILED", "WAITING_USER", "WAITING_EXTERNAL", "BUDGET_STOP"}
APPROVAL_TASKS = {"source_reuse_decision", "sea_submission", "pharmmapper_submission"}
EXTERNAL_TASKS = {"sea_collect", "pharmmapper_collect"}
RETRYABLE_STATES = {"QUEUED", "READY_FOR_WORKER", "RETRY_WAIT"}
ACCEPTED_DEPENDENCY_STATES = {"DONE", "DONE_RAW_UNVERIFIED"}
ALLOWED_TRANSITIONS = {
    "QUEUED": {"READY_FOR_WORKER", "WAITING_EXTERNAL", "WAITING_USER", "DONE", "DONE_RAW_UNVERIFIED"},
    "READY_FOR_WORKER": {"RUNNING", "RETRY_WAIT", "FAILED", "DONE", "DONE_RAW_UNVERIFIED", "WAITING_EXTERNAL", "WAITING_USER"},
    "RUNNING": {"DONE", "DONE_RAW_UNVERIFIED", "RETRY_WAIT", "FAILED", "WAITING_EXTERNAL", "WAITING_USER"},
    "RETRY_WAIT": {"READY_FOR_WORKER", "RUNNING", "FAILED", "WAITING_EXTERNAL"},
    "WAITING_EXTERNAL": {"READY_FOR_WORKER", "RUNNING", "DONE", "DONE_RAW_UNVERIFIED", "FAILED", "WAITING_USER"},
    "WAITING_USER": {"READY_FOR_WORKER", "RUNNING", "DONE", "FAILED"},
    "DONE_RAW_UNVERIFIED": {"DONE", "WAITING_EXTERNAL", "FAILED"},
    "FAILED": {"RETRY_WAIT", "READY_FOR_WORKER"},
    "DONE": set(),
}

def transition_task(task: dict[str, Any], new_status: str) -> None:
    """Apply one auditable status transition; reject impossible jumps."""
    current = str(task.get("status", "QUEUED"))
    if current == new_status:
        return
    if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"invalid task transition: {current} -> {new_status}")
    task["status"] = new_status

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def write_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)

def ingest_external_events(run: Path) -> list[dict[str, Any]]:
    """Record newly uploaded artifacts so they cannot be silently ignored."""
    incoming = run / "incoming"
    if not incoming.is_dir():
        return []
    manifest_path = run / "external_event_manifest.json"
    manifest = read(manifest_path, {"events": []})
    known = {str(item.get("sha256")) for item in manifest.get("events", [])}
    added = []
    for path in sorted(incoming.iterdir()):
        if not path.is_file():
            continue
        digest_value = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest_value in known:
            continue
        stem = path.stem.lower()
        provider = "pharmmapper" if "pharm" in stem else ("sea" if "sea" in stem else "unknown")
        event = {"event_id": f"external-{digest_value[:12]}", "event_type": "EXTERNAL_DATA_RECEIVED", "provider": provider, "path": str(path), "sha256": digest_value, "received_at_utc": now(), "status": "RECEIVED", "next_action": "schema 검사와 domain 변환 worker dispatch"}
        manifest.setdefault("events", []).append(event)
        added.append(event)
        append_event(run / "event_log.jsonl", event)
    if added:
        write_atomic(manifest_path, manifest)
    return added

def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def task_map(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {task["id"]: task for task in queue.get("tasks", [])}

def validate_queue_contract(queue: dict[str, Any]) -> list[str]:
    """Return structural queue errors before a controller can dispatch work."""
    tasks = task_map(queue)
    errors=[]
    for task in queue.get("tasks", []):
        if not task.get("id"):
            errors.append("task without id")
        if task.get("status") not in {"QUEUED", "READY_FOR_WORKER", "RUNNING", "RETRY_WAIT", "DONE", "DONE_RAW_UNVERIFIED", "WAITING_USER", "WAITING_EXTERNAL", "WAITING_MAPPING_QC", "FAILED", "BLOCKED", "INVALIDATED", "IDENTITY_MISMATCH", "NEEDS_EXTERNAL_SUBMISSION", "CAPTCHA_CONFIRMATION_REQUIRED"}:
            errors.append(f"{task.get('id')}: unknown status {task.get('status')}")
        for dep in task.get("requires", []):
            if dep not in tasks:
                errors.append(f"{task.get('id')}: missing dependency {dep}")
    return errors

def reconcile_queue(run: Path, queue: dict[str, Any], expected_cid: str | None = None) -> dict[str, Any]:
    """Repair queue state from durable provider ledgers and verified artifact paths.

    A provider completion is an event, not a chat message.  This function makes
    that event idempotent: it promotes matching submission/collection tasks,
    blocks CID mismatches, and leaves missing artifacts waiting for retrieval.
    """
    ledger = read(run / "job_ledger.json", {})
    tasks = task_map(queue)
    changes: list[dict[str, Any]] = []

    # Wake external-wait tasks when the required local service is available.
    # A prior WAITING_EXTERNAL state must never become a silent terminal state.
    cytoscape_task = tasks.get("cytoscape_visualization")
    if cytoscape_task and cytoscape_task.get("status") == "WAITING_EXTERNAL":
        try:
            with urllib.request.urlopen("http://127.0.0.1:1234/v1/version", timeout=1) as response:
                online = response.status == 200
        except Exception:
            online = False
        if online:
            cytoscape_task.update({
                "status": "READY_FOR_WORKER",
                "detail": "Cytoscape/cyREST 연결 확인; worker 재개",
                "next_action": "dispatch registered worker and verify its artifact contract",
            })
            cytoscape_task.pop("next_attempt_at", None)
            changes.append({"task": "cytoscape_visualization", "status": "READY_FOR_WORKER", "event": "external_dependency_recovered"})
    # Migrate legacy queues that predate the explicit analysis fan-out.  This
    # prevents a completed PPI worker from being orphaned behind final_ppi.
    if "initial_ppi" in tasks:
        specs = [
            ("overlap_analysis", "agent3", ["initial_ppi"]),
            ("ppi_analysis", "agent3", ["initial_ppi"]),
            ("enrichment_analysis", "agent3", ["ppi_analysis"]),
            ("integration_analysis", "agent3", ["overlap_analysis", "ppi_analysis", "enrichment_analysis"]),
        ]
        for task_id, agent, requires in specs:
            if task_id not in tasks:
                task = {"id": task_id, "agent": agent, "requires": requires, "status": "QUEUED", "info": {}, "attempts": 0}
                queue.setdefault("tasks", []).append(task); tasks[task_id] = task
                changes.append({"task": task_id, "status": "QUEUED", "event": "legacy_queue_migrated"})
        if "final_ppi" in tasks and tasks["final_ppi"].get("requires") == ["initial_ppi"]:
            tasks["final_ppi"]["requires"] = ["integration_analysis"]
            if tasks["final_ppi"].get("status") == "QUEUED":
                tasks["final_ppi"]["detail"] = "analysis fan-out migrated"
            changes.append({"task": "final_ppi", "requires": ["integration_analysis"], "event": "legacy_queue_migrated"})
        tail_specs = [
            ("experimental_evidence_synthesis", "agent4", ["independent_qc"]),
            ("mechanism_enrichment_synthesis", "agent4", ["enrichment_analysis", "experimental_evidence_synthesis"]),
            ("cytoscape_visualization", "agent3", ["final_ppi", "independent_qc"]),
            ("figure_draft", "agent5", ["cytoscape_visualization", "mechanism_enrichment_synthesis", "independent_qc"]),
            ("docking_candidate_selection", "agent7", ["cytoscape_visualization", "mechanism_enrichment_synthesis", "experimental_evidence_synthesis", "figure_draft"]),
            ("methods_results_draft", "agent5", ["docking_candidate_selection", "figure_draft", "mechanism_enrichment_synthesis"]),
            ("manuscript_review", "agent5", ["methods_results_draft"]),
            ("completion_packager", "agent5", ["manuscript_review", "methods_results_draft", "figure_draft"]),
        ]
        for task_id, agent, requires in tail_specs:
            if task_id not in tasks:
                task = {"id": task_id, "agent": agent, "requires": requires, "status": "QUEUED", "info": {}, "attempts": 0}
                queue.setdefault("tasks", []).append(task); tasks[task_id] = task
                changes.append({"task": task_id, "status": "QUEUED", "event": "legacy_queue_tail_migrated"})
    # A code fix or newly granted external approval must wake a previously
    # terminal worker.  Leaving FAILED in place makes the controller look
    # alive while no work can ever be dispatched.
    approval = read(run / "external_access_approval.json", {})
    for task_id in ("initial_ppi", "ppi_analysis"):
        task = tasks.get(task_id)
        if not task:
            continue
        if task.get("status") == "FAILED" and (run / "external_action_request.json").is_file():
            task["status"] = "WAITING_USER"
            task["detail"] = "외부 전송 게이트가 생성되어 승인 대기로 복구"
            changes.append({"task": task_id, "status": "WAITING_USER"})
        if task.get("status") == "WAITING_USER" and approval.get("approved") is True:
            task["status"] = "READY_FOR_WORKER"
            task["attempts"] = 0
            task.pop("next_attempt_at", None)
            task["detail"] = "외부 전송 승인 확인; worker 재개"
            changes.append({"task": task_id, "status": "READY_FOR_WORKER"})
    accepted = {"SUBMITTED", "RETRIEVED", "RETRIEVED_UNVERIFIED", "VERIFIED",
                "RESULT_FILE_RECEIVED_UNVERIFIED", "SUBMITTED_AWAITING_RESULT"}
    for provider, collect_id in (("sea", "sea_collect"), ("pharmmapper", "pharmmapper_collect")):
        submission_id = f"{provider}_submission"
        row = ledger.get(submission_id, {})
        if not row or not row.get("job_id"):
            continue
        observed_cid = str(row.get("cid") or row.get("file_cid") or "")
        mismatch = bool(expected_cid and observed_cid and observed_cid != str(expected_cid))
        if mismatch:
            for task_id in (submission_id, collect_id):
                if task_id in tasks and tasks[task_id].get("status") != "IDENTITY_MISMATCH":
                    tasks[task_id].update({"status": "IDENTITY_MISMATCH", "detail": f"provider CID {observed_cid} != run CID {expected_cid}"})
                    changes.append({"task": task_id, "status": "IDENTITY_MISMATCH"})
            continue
        if row.get("status") in accepted and submission_id in tasks and tasks[submission_id].get("status") != "DONE":
            tasks[submission_id].update({"status": "DONE", "info": {"job_id": row.get("job_id"), "provider_status": row.get("status")}})
            changes.append({"task": submission_id, "status": "DONE"})
        artifact = row.get("raw_file") or row.get("result_file")
        if collect_id in tasks and artifact and Path(str(artifact)).is_file() and tasks[collect_id].get("status") not in {"DONE", "DONE_RAW_UNVERIFIED"}:
            tasks[collect_id].update({"status": "DONE_RAW_UNVERIFIED", "info": {"job_id": row.get("job_id"), "artifact": str(artifact), "qc_status": "UNVERIFIED"}})
            changes.append({"task": collect_id, "status": "DONE_RAW_UNVERIFIED"})
    if changes:
        append_event(run / "event_log.jsonl", {"event": "queue_reconciled", "changes": changes})
    return queue

def ready_tasks(queue: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = task_map(queue)
    ready = []
    for task in queue.get("tasks", []):
        if task.get("status") not in {"QUEUED", "READY_FOR_WORKER", "RETRY_WAIT"}:
            continue
        deps = [tasks[name] for name in task.get("requires", []) if name in tasks]
        if task.get("status") == "RETRY_WAIT":
            next_at = task.get("next_attempt_at")
            if next_at:
                try:
                    if dt.datetime.fromisoformat(next_at) > dt.datetime.now(dt.timezone.utc):
                        continue
                except ValueError:
                    pass
        if all(dep.get("status") in ACCEPTED_DEPENDENCY_STATES for dep in deps):
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
    terminal_required = ["independent_qc", "manuscript_review", "cytoscape_visualization", "docking_candidate_selection", "figure_draft", "methods_results_draft", "completion_packager"]
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
            ingest_external_events(run)
            # Boundary worker: validate/archive uploads and notify the domain
            # collector before queue synchronization can consume them.
            import event_agent
            event_agent.route_external_events(run)
            import np_agent_queue
            np_agent_queue.collect(run)
            queue = read(queue_path, queue)
            expected_cid = str(read(run / "structure_manifest.json", {}).get("cid") or "") or None
            queue = reconcile_queue(run, queue, expected_cid=expected_cid)
            # A fresh provider bundle creates an explicit mapping gate.  Once
            # both branches are present, promote that gate to the registered
            # local worker instead of leaving the controller idle forever.
            tasks = task_map(queue)
            mapping_task = tasks.get("initial_ppi")
            if mapping_task and mapping_task.get("status") == "WAITING_MAPPING_QC":
                deps = [tasks.get(name, {}).get("status") for name in mapping_task.get("requires", [])]
                if deps and all(status in {"DONE", "DONE_RAW_UNVERIFIED"} for status in deps):
                    mapping_task.update({"status": "READY_FOR_WORKER", "detail": "provider 원본 확보됨; UniProt 안정 ID 매핑 worker 실행"})
                    append_event(run / "event_log.jsonl", {"event": "mapping_gate_released", "task_id": "initial_ppi"})
            write_atomic(queue_path, queue)
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
            task.update({"status": "WAITING_EXTERNAL", "next_action": "check PharmMapper Check Job or provider official status using recorded job ID"})
        else:
            task.update({"status": "READY_FOR_WORKER", "next_action": "dispatch registered worker and verify its artifact contract"})
    if not dry_run:
        write_atomic(queue_path, queue)
    state.pop("last_error", None)
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
