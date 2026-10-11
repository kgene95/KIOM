"""계획 밖 외부자료·추가업무 이벤트 전담 세부 에이전트."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .np_workers import external_data_intake
    from .state_store import append_event, now_utc, save_json_atomic
except ImportError:
    from np_workers import external_data_intake
    from state_store import append_event, now_utc, save_json_atomic


def route_external_events(run: Path) -> dict[str, Any]:
    """검수 worker를 호출하고 계획 밖 이벤트의 route/handoff를 확정한다."""
    intake = external_data_intake(run)
    manifest_path = run / "external_validation_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError):
        manifest = {"files": []}
    report_path = run / "event_agent_report.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError):
        report = {"agent": "event_agent", "routes": []}
    known = {item.get("sha256") for item in report.get("routes", [])}
    routes = []
    for item in manifest.get("files", []):
        if item.get("sha256") in known:
            continue
        # The generic router must not know domain/provider-specific task names.
        # Domain adapters declare the receiver in the validated manifest; if
        # absent, hand the event to the controller for explicit routing.
        recipient = item.get("next_worker") or item.get("recipient_worker") or "controller"
        original_task = item.get("original_task") or item.get("source_task") or recipient
        route = {
            "event_type": "EXTERNAL_DATA_VALIDATED",
            "sha256": item.get("sha256"),
            "provider": item.get("provider"),
            "source": item.get("archived_path") or item.get("path"),
            "recipient_worker": recipient,
            "original_task": original_task,
            "status": item.get("status"),
            "next_action": "수신 worker가 handoff를 소비하고 재맵핑·재실행",
            "routed_utc": now_utc(),
        }
        report.setdefault("routes", []).append(route)
        routes.append(route)
        append_event(run, {"event": "event_agent_routed", **route})
    save_json_atomic(report_path, report)
    status = "DONE" if intake.get("status") == "DONE" else intake.get("status", "WAITING_EXTERNAL")
    return {"task_id": "event_agent_router", "status": status, "routes": routes,
            "outputs": ["event_agent_report.json", "external_validation_manifest.json"],
            "next_action": "총괄이 route report와 수신 worker 결과를 확인"}

