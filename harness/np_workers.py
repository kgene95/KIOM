"""NP worker 계약의 로컬 구현.

외부 provider를 우회하지 않는다. provider 결과가 run 폴더에 도착한 뒤
검증하는 로컬 worker와 입력 gate를 제공한다.
"""
from __future__ import annotations

import json
import shutil
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


def disease_target_collection(run: Path) -> dict[str, Any]:
    """Open Targets 질환 표적 branch를 수집하고 입력 hash 전 단계 manifest를 남긴다."""
    existing = _load(run, "disease_target_manifest.json", {}) or {}
    if existing.get("verified") is True and existing.get("file") and Path(existing["file"]).is_file():
        return _write(run, "disease_target_collection", "DONE", outputs=[existing["file"]])
    request = _load(run, "request.json", {}) or {}
    disease = request.get("disease_input")
    species = request.get("species")
    if not disease or species != "Homo sapiens":
        return _write(run, "disease_target_collection", "WAITING_USER", next_action="질환명과 Homo sapiens 입력 확인")
    try:
        from providers import opentargets_disease_targets
        rows, metadata = opentargets_disease_targets(disease)
    except Exception as exc:
        return _write(run, "disease_target_collection", "FAILED_RETRYABLE", next_action="Open Targets 조회를 bounded retry", reason=str(exc)[:220])
    output = run / "source_archive" / "OpenTargets" / "disease_targets.json"
    save_json_atomic(output, {"rows": rows, "metadata": metadata, "retrieved_utc": now_utc()})
    manifest = {"verified": True, "ontology_id": metadata.get("disease_id"), "file": str(output),
                "rows": len(rows), "species": species, "source": "Open Targets Platform GraphQL",
                "retrieved_utc": now_utc()}
    save_json_atomic(run / "disease_target_manifest.json", manifest)
    return _write(run, "disease_target_collection", "DONE", outputs=["disease_target_manifest.json", str(output.relative_to(run))])


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


def _collect_provider(run: Path, task_id: str, provider: str) -> dict[str, Any]:
    ledger = _load(run, "job_ledger.json", {}) or {}
    row = ledger.get(f"{provider}_submission", {})
    raw_file = row.get("raw_file")
    if not row.get("job_id"):
        return _write(run, task_id, "WAITING_EXTERNAL", next_action=f"{provider} job ID 대기")
    if not raw_file:
        return _write(run, task_id, "WAITING_EXTERNAL", next_action=f"{provider} 공식 raw 결과 대기")
    path = Path(raw_file)
    if not path.is_file():
        return _write(run, task_id, "WAITING_EXTERNAL", next_action="공식 결과 파일 수신 대기")
    actual = file_sha256(path)
    if row.get("sha256") and row["sha256"] != actual:
        return _write(run, task_id, "CORRECT_AND_RERUN", next_action="job ledger SHA를 수정하지 말고 공식 raw 파일을 재확인", reason="raw SHA-256 mismatch")
    manifest = {"provider": provider, "job_id": row["job_id"], "raw_file": str(path), "sha256": actual,
                "verified": True, "updated_utc": now_utc()}
    name = f"{provider}_result_manifest.json"
    save_json_atomic(run / name, manifest)
    return _write(run, task_id, "DONE", outputs=[name])


def sea_collect(run: Path) -> dict[str, Any]:
    return _collect_provider(run, "sea_collect", "sea")


def pharmmapper_collect(run: Path) -> dict[str, Any]:
    return _collect_provider(run, "pharmmapper_collect", "pharmmapper")


def ppi_analysis(run: Path) -> dict[str, Any]:
    manifest = _load(run, "ppi_manifest.json", {}) or {}
    network_file = manifest.get("network_file")
    if not network_file or not Path(network_file).is_file():
        return _write(run, "ppi_analysis", "WAITING_EXTERNAL", next_action="검증된 PPI network_file 대기")
    if not manifest.get("input_sha256"):
        return _write(run, "ppi_analysis", "CORRECT_AND_RERUN", next_action="PPI 입력 hash 기록", reason="input_sha256 missing")
    return _write(run, "ppi_analysis", "DONE", outputs=[str(network_file)])


def enrichment_analysis(run: Path) -> dict[str, Any]:
    manifest = _load(run, "enrichment_manifest.json", {}) or {}
    output = manifest.get("output_file")
    if not output or not Path(output).is_file():
        return _write(run, "enrichment_analysis", "WAITING_EXTERNAL", next_action="enrichment 결과 파일 대기")
    if not manifest.get("input_sha256"):
        return _write(run, "enrichment_analysis", "CORRECT_AND_RERUN", next_action="enrichment 입력 hash 기록", reason="input_sha256 missing")
    return _write(run, "enrichment_analysis", "DONE", outputs=[str(output)])


def integration_analysis(run: Path) -> dict[str, Any]:
    required = ["overlap_analysis", "ppi_analysis", "enrichment_analysis"]
    results = [_load(run, f"worker_results/{name}.json", {}) or {} for name in required]
    if any(item.get("status") != "DONE" for item in results):
        return _write(run, "integration_analysis", "WAITING_EXTERNAL", next_action="overlap·PPI·enrichment worker 완료 대기")
    return _write(run, "integration_analysis", "DONE", outputs=[f"worker_results/{name}.json" for name in required])


def independent_qc(run: Path) -> dict[str, Any]:
    result = _load(run, "worker_results/integration_analysis.json", {}) or {}
    if result.get("status") != "DONE":
        return _write(run, "independent_qc", "WAITING_EXTERNAL", next_action="통합 분석 완료 대기")
    qc = {"verdict": "PASS", "basis": "integration worker outputs present", "updated_utc": now_utc()}
    save_json_atomic(run / "independent_qc.json", qc)
    return _write(run, "independent_qc", "DONE", outputs=["independent_qc.json"])


def manuscript_review(run: Path) -> dict[str, Any]:
    qc = _load(run, "independent_qc.json", {}) or {}
    if qc.get("verdict") != "PASS":
        return _write(run, "manuscript_review", "WAITING_EXTERNAL", next_action="독립 QC PASS 대기")
    review = {"status": "REVIEWED", "basis": "independent QC PASS", "updated_utc": now_utc()}
    save_json_atomic(run / "manuscript_review.json", review)
    return _write(run, "manuscript_review", "DONE", outputs=["manuscript_review.json"])


def completion_packager(run: Path) -> dict[str, Any]:
    if (_load(run, "independent_qc.json", {}) or {}).get("verdict") != "PASS":
        return _write(run, "completion_packager", "WAITING_EXTERNAL", next_action="독립 QC PASS 대기")
    if (_load(run, "manuscript_review.json", {}) or {}).get("status") != "REVIEWED":
        return _write(run, "completion_packager", "WAITING_EXTERNAL", next_action="원고 검토 완료 대기")
    package = {"profile": "results_plus_manifest", "run_id": run.name, "created_utc": now_utc(),
               "files": ["independent_qc.json", "manuscript_review.json"]}
    save_json_atomic(run / "completion_manifest.json", package)
    return _write(run, "completion_packager", "DONE", outputs=["completion_manifest.json"])
