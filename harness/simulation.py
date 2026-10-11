"""Deterministic, offline harness simulation for regression testing.

The simulation never contacts external providers.  It injects a deliberately
wrong SEA artifact, verifies that the external-event worker quarantines it,
then injects the corrected artifact and runs the downstream analysis fan-out.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _event(run: Path, name: str, **payload: Any) -> None:
    with (run / "event_log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": name, **payload}, ensure_ascii=False) + "\n")


def _csv(path: Path, cid: str, compound: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["compound", "cid", "target_id", "score"])
        writer.writeheader()
        writer.writerow({"compound": compound, "cid": cid, "target_id": "9606", "score": "0.91"})


def _read_events(run: Path) -> list[str]:
    return [json.loads(line)["event"] for line in (run / "event_log.jsonl").read_text(encoding="utf-8").splitlines() if line]


def run_simulation(root: Path) -> dict[str, Any]:
    run = root / "virtual_np_run_A_B_disease_X"
    incoming = run / "incoming"
    archive = run / "source_archive"
    quarantine = run / "quarantine"
    incoming.mkdir(parents=True, exist_ok=True)
    archive.mkdir(parents=True, exist_ok=True)
    _write_json(run / "request.json", {"compounds": [{"name": "A", "cid": "SIM-A"}, {"name": "B", "cid": "SIM-B"}], "disease": "X"})
    _event(run, "simulation_started", compounds=["A", "B"], disease="X")

    # The first B upload is intentionally a name-similar but wrong compound.
    wrong = incoming / "SEA_B_wrong.csv"
    _csv(wrong, "SIM-B-WRONG", "B-like")
    _event(run, "external_data_received", provider="SEA", compound="B", path=str(wrong))
    expected_cid = "SIM-B"
    with wrong.open(newline="", encoding="utf-8") as handle:
        observed_wrong = next(csv.DictReader(handle))["cid"]
    if observed_wrong != expected_cid:
        quarantine.mkdir(parents=True, exist_ok=True)
        wrong_target = quarantine / wrong.name
        wrong.replace(wrong_target)
        _write_json(run / "external_validation_manifest.json", {"status": "IDENTITY_MISMATCH", "expected_cid": expected_cid, "observed": observed_wrong, "quarantined": str(wrong_target), "sha256": _sha(wrong_target)})
        _event(run, "external_event_rejected", provider="SEA", reason="CID mismatch", expected=expected_cid, observed=observed_wrong, quarantined=str(wrong_target))
        wrong_status = "IDENTITY_MISMATCH"
    else:
        wrong_status = "UNEXPECTED_ACCEPT"

    # Corrected upload arrives as a new event; the rejected artifact remains immutable.
    correct = incoming / "SEA_B_correct.csv"
    _csv(correct, "SIM-B", "B")
    _event(run, "external_data_received", provider="SEA", compound="B", path=str(correct))
    with correct.open(newline="", encoding="utf-8") as handle:
        observed_correct = next(csv.DictReader(handle))["cid"]
    if observed_correct != expected_cid:
        raise AssertionError("corrected simulation input did not contain expected CID")
    stored = archive / "SEA_B_SIM-B.csv"
    correct.replace(stored)
    _write_json(run / "external_validation_manifest.json", {"status": "DONE", "expected_cid": expected_cid, "observed": expected_cid, "archived": str(stored), "sha256": _sha(stored)})
    _event(run, "external_event_validated", provider="SEA", compound="B", sha256=_sha(stored))
    _event(run, "external_event_routed", recipient="sea_collect", source=str(stored))

    # The simulation must validate the real queue/registry tail, not only
    # manufacture final-looking files.  This prevents a synthetic pass when
    # Cytoscape, docking handoff, or manuscript drafting is absent in runtime.
    required_tail = ["cytoscape_visualization", "docking_candidate_selection", "methods_results_draft", "completion_packager"]
    registry_path = Path(__file__).with_name("worker_registry.json")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    workers = registry.get("workers", {})
    planned = registry.get("planned_workers", {})
    missing_tail = [name for name in required_tail if name not in workers or planned.get(name, {}).get("status") not in {"implemented", "verified"}]
    if missing_tail:
        _event(run, "simulation_dispatch_contract_failed", missing=missing_tail)
        raise AssertionError(f"runtime tail workers are not dispatchable: {missing_tail}")
    _event(run, "simulation_dispatch_contract_validated", tasks=required_tail)

    # Offline downstream fan-out: target collection, PPI, enrichment, figure, docking.
    targets = run / "normalized_targets.csv"
    _csv(targets, "SIM-B", "B")
    _write_json(run / "analysis_summary.json", {"compounds": ["A", "B"], "disease": "X", "status": "DONE", "inputs": [str(stored), str(targets)]})
    _write_json(run / "figure_draft.json", {"type": "network_pharmacology_overview", "nodes": ["A", "B", "X"], "edges": 3, "status": "DRAFT"})
    _write_json(run / "docking_candidates.json", {"status": "CONFIRMED", "candidates": [{"compound": "B", "target": "SIM-TARGET-1", "rank": 1}, {"compound": "A", "target": "SIM-TARGET-2", "rank": 2}]})
    for worker in ("target_collection", "ppi_analysis", "enrichment_analysis", "figure_draft", "docking_candidate_selection", "methods_results_draft", "completion_packager"):
        _event(run, "worker_completed", worker=worker)
    _event(run, "simulation_recovered", recovery="wrong SEA B upload quarantined and corrected upload routed")
    _event(run, "simulation_completed", status="DONE")
    return {"status": "DONE", "wrong_upload_status": wrong_status, "correct_upload_status": "DONE", "events": _read_events(run), "artifacts": {"analysis_summary": run / "analysis_summary.json", "figure_draft": run / "figure_draft.json", "docking_candidates": run / "docking_candidates.json", "quarantine": quarantine}}
