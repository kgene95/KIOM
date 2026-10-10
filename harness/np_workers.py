"""NP worker 계약의 로컬 구현.

외부 provider를 우회하지 않는다. provider 결과가 run 폴더에 도착한 뒤
검증하는 로컬 worker와 입력 gate를 제공한다.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .state_store import append_event, now_utc, save_json_atomic
    from .verifier import file_sha256
except ImportError:  # 직접 실행/dispatcher 경로
    from state_store import append_event, now_utc, save_json_atomic
    from verifier import file_sha256


def _write(run: Path, task_id: str, status: str, *, next_action: str = "", outputs: list[str] | None = None, reason: str = "") -> dict[str, Any]:
    result = {"task_id": task_id, "status": status, "outputs": outputs or [], "reason": reason,
              "next_action": next_action, "updated_utc": now_utc()}
    save_json_atomic(run / "worker_results" / f"{task_id}.json", result)
    append_event(run, {"event": "worker_result", "task_id": task_id, "status": status})
    return result


def _load(run: Path, name: str, default: Any = None) -> Any:
    try:
        return json.loads((run / name).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def compound_identity(run: Path) -> dict[str, Any]:
    request = _load(run, "request.json", {}) or {}
    required = ["compound_input", "disease_input", "species"]
    missing = [key for key in required if not request.get(key)]
    if missing:
        return _write(run, "compound_identity", "WAITING_USER", next_action="필수 입력을 기록", reason=", ".join(missing))
    output = run / "worker_results" / "compound_identity.json"
    payload = {key: request[key] for key in required}
    payload.update({key: request[key] for key in ("compound_cid", "compound_smiles", "compound_inchikey") if request.get(key)})
    save_json_atomic(output, payload)
    return _write(run, "compound_identity", "DONE", outputs=[str(output.relative_to(run))])


def structure_qc(run: Path) -> dict[str, Any]:
    manifest = _load(run, "structure_manifest.json", {}) or {}
    path = manifest.get("structure_file")
    if not path:
        return _write(run, "structure_qc", "WAITING_EXTERNAL", next_action="검증된 structure_manifest.json 대기")
    structure = Path(path)
    if not structure.is_file():
        return _write(run, "structure_qc", "CORRECT_AND_RERUN", next_action="구조 파일 경로 수정", reason="structure file missing")
    expected = manifest.get("structure_sha256")
    actual = file_sha256(structure)
    if expected and expected != actual:
        return _write(run, "structure_qc", "CORRECT_AND_RERUN", next_action="구조 manifest와 파일을 일치시킨 뒤 재실행", reason="SHA-256 mismatch")
    return _write(run, "structure_qc", "DONE", outputs=[str(structure)])


def source_audit(run: Path) -> dict[str, Any]:
    choice = _load(run, "source_choice.json", {}) or {}
    if choice.get("decision") not in {"REUSE_VERIFIED", "RECOLLECT_NEW"} or choice.get("user_approved") is not True:
        return _write(run, "source_audit", "WAITING_USER", next_action="기존 자료 재사용 또는 신규 수집을 승인")
    return _write(run, "source_audit", "DONE", outputs=["source_choice.json"])


def normalize_targets(run: Path) -> dict[str, Any]:
    manifest = _load(run, "normalized_targets.json", {}) or {}
    if manifest.get("verified") is not True:
        return _write(run, "normalize_targets", "WAITING_EXTERNAL", next_action="stable-ID/species QC 결과 대기")
    return _write(run, "normalize_targets", "DONE", outputs=["normalized_targets.json"])


def overlap_analysis(run: Path) -> dict[str, Any]:
    manifest = _load(run, "overlap_manifest.json", {}) or {}
    if manifest.get("verified") is not True:
        return _write(run, "overlap_analysis", "WAITING_EXTERNAL", next_action="compound/disease target branch 검증 대기")
    return _write(run, "overlap_analysis", "DONE", outputs=["overlap_manifest.json"])
