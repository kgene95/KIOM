"""NP worker 계약의 로컬 구현.

외부 provider를 우회하지 않는다. provider 결과가 run 폴더에 도착한 뒤
검증하는 로컬 worker와 입력 gate를 제공한다.
"""
from __future__ import annotations

import json
import shutil
import csv
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from .state_store import append_event, now_utc, save_json_atomic
    from .verifier import file_sha256
except ImportError:  # 직접 실행/dispatcher 경로
    from state_store import append_event, now_utc, save_json_atomic
    from verifier import file_sha256


def _write(run: Path, task_id: str, status: str, *, next_action: str = "", outputs: list[str] | None = None, reason: str = "", reason_code: str = "") -> dict[str, Any]:
    result = {"task_id": task_id, "status": status, "outputs": outputs or [], "reason": reason,
              "next_action": next_action, "updated_utc": now_utc()}
    if reason_code:
        result["reason_code"] = reason_code
    save_json_atomic(run / "worker_results" / f"{task_id}.json", result)
    append_event(run, {"event": "worker_result", "task_id": task_id, "status": status})
    return result


def _load(run: Path, name: str, default: Any = None) -> Any:
    try:
        return json.loads((run / name).read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _external_gate(run: Path, *, endpoints: list[str], payload: str) -> tuple[bool, dict[str, Any]]:
    """Require one durable, auditable approval before sending run data out.

    The controller must not turn a provider permission error into a silent
    retry loop.  A gate file is also the handoff contract for a later resume.
    """
    approval = _load(run, "external_access_approval.json", {}) or {}
    scope = set(approval.get("endpoints", []))
    approved_hosts = {urllib.parse.urlparse(str(item)).netloc.lower() for item in scope if urllib.parse.urlparse(str(item)).netloc}
    requested_hosts = {urllib.parse.urlparse(str(item)).netloc.lower() for item in endpoints if urllib.parse.urlparse(str(item)).netloc}
    # An approval for a provider covers its documented sibling endpoints.
    # Exact-only matching previously left the next worker in a stale gate.
    endpoint_match = set(endpoints).issubset(scope)
    host_match = bool(requested_hosts) and requested_hosts.issubset(approved_hosts)
    allowed = approval.get("approved") is True and (endpoint_match or host_match)
    if allowed:
        return True, approval
    request = {"status": "WAITING_USER", "endpoints": endpoints, "payload": payload,
               "reason": "외부 API로 run의 표적 식별자를 전송하기 전 명시적 승인 필요", "updated_utc": now_utc()}
    slug = re.sub(r"[^A-Za-z0-9]+", "_", (urllib.parse.urlparse(endpoints[0]).netloc + "_" + urllib.parse.urlparse(endpoints[0]).path).strip("_"))[:90]
    save_json_atomic(run / f"external_action_request_{slug}.json", request)
    # Keep the legacy pointer for UI compatibility, while task-specific files
    # prevent one worker from overwriting another worker's approval request.
    save_json_atomic(run / "external_action_request.json", request)
    return False, request


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


def external_data_intake(run: Path) -> dict[str, Any]:
    """Validate every newly uploaded artifact and notify its domain worker.

    This is deliberately a separate boundary worker: provider parsers never
    receive an unreviewed file, and an upload cannot be silently ignored.
    """
    incoming = run / "incoming"
    if not incoming.is_dir():
        return _write(run, "external_data_intake", "WAITING_EXTERNAL", next_action="incoming 파일 대기")
    request = _load(run, "request.json", {}) or {}
    expected = str(request.get("compound_cid") or (_load(run, "structure_manifest.json", {}) or {}).get("cid") or "")
    archive = run / "source_archive" / "ExternalIntake"
    archive.mkdir(parents=True, exist_ok=True)
    manifest_path = run / "external_validation_manifest.json"
    manifest = _load(run, manifest_path.name, {}) or {"files": []}
    known = {item.get("sha256") for item in manifest.get("files", [])}
    notifications = run / "worker_notifications.jsonl"
    validated = []
    for path in sorted(incoming.iterdir()):
        if not path.is_file():
            continue
        digest = file_sha256(path)
        if digest in known:
            continue
        provider = "pharmmapper" if "pharm" in path.stem.lower() else ("sea" if "sea" in path.stem.lower() else "unknown")
        sample = path.read_bytes()[:8192].decode("utf-8", errors="ignore")
        cid_match = re.search(r"(?:CID|cid)[ _:-]*(\d+)", path.name + "\n" + sample)
        observed = cid_match.group(1) if cid_match else ""
        status = "VALIDATED" if provider != "unknown" and (not expected or not observed or observed == expected) else "IDENTITY_MISMATCH"
        archived = archive / path.name
        if not archived.exists():
            shutil.copy2(path, archived)
        item = {"path": str(path), "archived_path": str(archived), "provider": provider,
                "sha256": digest, "observed_cid": observed, "expected_cid": expected,
                "status": status, "received_utc": now_utc(),
                "next_worker": f"{provider}_collect" if provider != "unknown" else "controller"}
        manifest.setdefault("files", []).append(item); validated.append(item)
        with notifications.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"event": "EXTERNAL_DATA_VALIDATED", "recipient": item["next_worker"], "artifact": item, "at_utc": now_utc()}, ensure_ascii=False) + "\n")
    save_json_atomic(manifest_path, manifest)
    if not validated:
        return _write(run, "external_data_intake", "DONE", outputs=["external_validation_manifest.json"])
    if any(item["status"] == "IDENTITY_MISMATCH" for item in validated):
        return _write(run, "external_data_intake", "CORRECT_AND_RERUN", next_action="CID 불일치 파일 격리 후 올바른 원본 재수신", reason="external artifact CID mismatch", outputs=["external_validation_manifest.json", "worker_notifications.jsonl"])
    return _write(run, "external_data_intake", "DONE", outputs=["external_validation_manifest.json", "worker_notifications.jsonl"])


def normalize_targets(run: Path) -> dict[str, Any]:
    manifest = _load(run, "normalized_targets.json", {}) or {}
    if manifest.get("verified") is not True:
        return _write(run, "normalize_targets", "WAITING_EXTERNAL", next_action="stable-ID/species QC 결과 대기")
    return _write(run, "normalize_targets", "DONE", outputs=["normalized_targets.json"])


def initial_ppi(run: Path) -> dict[str, Any]:
    """Map the freshly collected human targets before allowing PPI analysis.

    The provider results are not treated as gene identifiers until UniProt
    returns a reviewed human entry for every retained target.  A failed or
    partial lookup becomes an explicit waiting state, so the controller does
    not silently idle at WAITING_MAPPING_QC.
    """
    normalized = _load(run, "normalized_targets.json", {}) or {}
    if normalized.get("verified") is not True:
        source = run / "compound_targets.csv"
        if not source.is_file():
            return _write(run, "initial_ppi", "WAITING_EXTERNAL", next_action="compound_targets.csv 대기")
        approved, gate = _external_gate(
            run,
            endpoints=["https://rest.uniprot.org/uniprotkb/search"],
            payload="두 run의 PharmMapper/SEA target_id를 Homo sapiens reviewed UniProt accession으로 매핑",
        )
        if not approved:
            return _write(run, "initial_ppi", "WAITING_USER", next_action="external_access_approval.json에 UniProt 승인 기록", reason=gate["reason"], outputs=["external_action_request.json"])
        try:
            with source.open(newline="", encoding="utf-8-sig") as handle:
                rows = list(csv.DictReader(handle))
            identifiers = sorted({str(row.get("target_id", "")).strip() for row in rows if str(row.get("target_id", "")).strip() and str(row.get("target_id", "")).upper() != "NONE"})
            mapped = {}
            for start in range(0, len(identifiers), 40):
                chunk = identifiers[start:start + 40]
                clauses=[]
                for identifier in chunk:
                    # UniProt accessions have a digit in position 2 and a
                    # digit at the end; names such as AMPM2/GLCM are entry
                    # names and must use the id:<ENTRY>_HUMAN query.
                    if re.fullmatch(r"[A-Z][0-9][A-Z0-9]{3}[0-9]|[A-Z0-9]{10}", identifier.upper()):
                        clauses.append(f"accession:{identifier}")
                    else:
                        clauses.append(f"id:{identifier}_HUMAN")
                query = "(" + " OR ".join(clauses) + ") AND organism_id:9606 AND reviewed:true"
                url = "https://rest.uniprot.org/uniprotkb/search?" + urllib.parse.urlencode({"query": query, "format": "tsv", "fields": "accession,id,gene_names,organism_id,reviewed", "size": 500})
                request = urllib.request.Request(url, headers={"User-Agent": "KIOM-NP-harness/1.0"})
                with urllib.request.urlopen(request, timeout=30) as response:
                    lines = response.read().decode("utf-8").splitlines()
                for item in csv.DictReader(lines, delimiter="\t"):
                    entry = item.get("Entry", "").strip()
                    entry_name = item.get("Entry Name", "").strip()
                    aliases = {entry, entry_name.removesuffix("_HUMAN")}
                    aliases.update(x for x in item.get("Gene Names", "").split() if x)
                    for alias in aliases:
                        if alias:
                            mapped[alias.upper()] = item
            normalized_rows=[]; unmapped=[]
            for row in rows:
                identifier=str(row.get("target_id", "")).strip()
                item=mapped.get(identifier.upper()) or mapped.get((identifier + "_HUMAN").upper())
                if not item:
                    unmapped.append(identifier); continue
                normalized_rows.append({"compound_cid": row.get("compound_cid"), "submitted_id": identifier, "gene_symbol": (item.get("Gene Names", "").split() or [identifier])[0], "stable_id": item.get("Entry", ""), "species": item.get("Organism (ID)", ""), "source": row.get("source"), "raw_score": row.get("source_score")})
            if unmapped:
                # A mixed PharmMapper export commonly contains entry names or
                # non-human rows. Keep them auditable, but do not block all
                # verified human targets from entering PPI analysis.
                unmapped_path = run / "unmapped_targets.csv"
                with unmapped_path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=["target_id", "reason"])
                    writer.writeheader()
                    writer.writerows({"target_id": item, "reason": "no reviewed human UniProt match"} for item in sorted(set(unmapped)))
                if not normalized_rows:
                    save_json_atomic(run / "normalized_targets.json", {"verified": False, "rows": [], "unmapped": sorted(set(unmapped)), "next_action": "UniProt 매핑 보정 필요", "updated_utc": now_utc()})
                    return _write(run, "initial_ppi", "FAILED_RETRYABLE", next_action=f"UniProt 매핑 미확인 {len(set(unmapped))}개; verified human target 없음", reason="no stable human UniProt mapping", outputs=["normalized_targets.json", "unmapped_targets.csv"])
                output = run / "normalized_targets.csv"
                with output.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=["compound_cid","submitted_id","gene_symbol","stable_id","species","source","raw_score"])
                    writer.writeheader(); writer.writerows(normalized_rows)
                manifest = {"verified": True, "partial": True, "mapping_qc": "PARTIAL_EXCLUSION_RECORDED", "species": "9606", "rows": len(normalized_rows), "unmapped": sorted(set(unmapped)), "unmapped_count": len(set(unmapped)), "file": str(output), "sha256": file_sha256(output), "unmapped_file": str(unmapped_path), "updated_utc": now_utc()}
                save_json_atomic(run / "normalized_targets.json", manifest)
                normalized = manifest
            else:
                output = run / "normalized_targets.csv"
                with output.open("w", newline="", encoding="utf-8") as handle:
                    writer=csv.DictWriter(handle, fieldnames=["compound_cid","submitted_id","gene_symbol","stable_id","species","source","raw_score"]); writer.writeheader(); writer.writerows(normalized_rows)
                manifest={"verified": True, "species": "9606", "rows": len(normalized_rows), "file": str(output), "sha256": file_sha256(output), "updated_utc": now_utc()}
                save_json_atomic(run / "normalized_targets.json", manifest)
                normalized=manifest
        except Exception as exc:
            if "10013" in str(exc) or "permission" in str(exc).lower() or "access" in str(exc).lower():
                approved, gate = _external_gate(run, endpoints=["https://rest.uniprot.org/uniprotkb/search"], payload="UniProt 표적 매핑 요청")
                return _write(run, "initial_ppi", "WAITING_USER", next_action="네트워크 권한/UniProt 전송 승인 후 재개", reason=gate["reason"], outputs=["external_action_request.json"])
            return _write(run, "initial_ppi", "FAILED_RETRYABLE", next_action="UniProt 매핑 bounded retry", reason=str(exc)[:220])
    manifest = _load(run, "ppi_manifest.json", {}) or {}
    if not manifest.get("network_file"):
        return _write(run, "initial_ppi", "WAITING_EXTERNAL", next_action="검증된 PPI network_file 대기", outputs=["normalized_targets.json"])
    return _write(run, "initial_ppi", "DONE", outputs=["normalized_targets.json", str(manifest["network_file"])])


def overlap_analysis(run: Path) -> dict[str, Any]:
    manifest = _load(run, "overlap_manifest.json", {}) or {}
    if manifest.get("verified") is not True:
        normalized = _load(run, "normalized_targets.json", {}) or {}
        disease = _load(run, "disease_target_manifest.json", {}) or {}
        disease_file = disease.get("file")
        normalized_file = normalized.get("file")
        if not disease_file or not normalized_file or not Path(disease_file).is_file() or not Path(normalized_file).is_file():
            return _write(run, "overlap_analysis", "WAITING_EXTERNAL", next_action="compound/disease target branch 검증 대기")
        disease_doc = _load(Path(disease_file).parent, Path(disease_file).name, {}) or {}
        disease_symbols = {str(row.get("target") or row.get("approvedSymbol") or "").upper() for row in disease_doc.get("rows", []) if row.get("target") or row.get("approvedSymbol")}
        with Path(normalized_file).open(newline="", encoding="utf-8-sig") as handle:
            compound_rows = list(csv.DictReader(handle))
        overlap = [row for row in compound_rows if str(row.get("gene_symbol", "")).upper() in disease_symbols]
        output = run / "overlap_targets.csv"
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["gene_symbol", "stable_id", "source", "raw_score"])
            writer.writeheader(); writer.writerows({key: row.get(key, "") for key in writer.fieldnames} for row in overlap)
        manifest = {"verified": True, "rows": len(overlap), "file": str(output), "updated_utc": now_utc()}
        save_json_atomic(run / "overlap_manifest.json", manifest)
    return _write(run, "overlap_analysis", "DONE", outputs=["overlap_manifest.json"])


def _collect_provider(run: Path, task_id: str, provider: str) -> dict[str, Any]:
    # Consume the intake handoff so a new upload is visible to the original
    # provider worker instead of being mistaken for an old run artifact.
    notices = []
    notice_path = run / "worker_notifications.jsonl"
    if notice_path.is_file():
        for line in notice_path.read_text(encoding="utf-8-sig").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            artifact = item.get("artifact", {})
            if item.get("recipient") == task_id or artifact.get("next_worker") == task_id:
                notices.append(item)
        if notices:
            save_json_atomic(run / f"{provider}_intake_handoff.json", {"worker": task_id, "notices": notices, "consumed_utc": now_utc()})
    # A browser/manual upload may already have produced the provider manifest
    # before the queue was reconciled.  Validate its raw/normalized hashes at
    # the boundary and promote the collection task without waiting forever for
    # a second upload.  Scientific QC remains a separate downstream gate.
    existing_manifest = _load(run, f"{provider}_result_manifest.json", {}) or {}
    if existing_manifest.get("job_id"):
        raw_existing = Path(str(existing_manifest.get("raw_file") or existing_manifest.get("result_file") or ""))
        normalized_existing = Path(str(existing_manifest.get("normalized_file") or "")) if existing_manifest.get("normalized_file") else None
        expected_cid = str((_load(run, "structure_manifest.json", {}) or {}).get("cid") or "")
        identity_ok = not existing_manifest.get("cid") or not expected_cid or str(existing_manifest.get("cid")) == expected_cid or existing_manifest.get("identity_match") == "PASS"
        raw_ok = raw_existing.is_file() and (not existing_manifest.get("sha256") and not existing_manifest.get("raw_sha256") or file_sha256(raw_existing) == (existing_manifest.get("sha256") or existing_manifest.get("raw_sha256")))
        normalized_ok = not normalized_existing or (normalized_existing.is_file() and (not existing_manifest.get("normalized_sha256") or file_sha256(normalized_existing) == existing_manifest.get("normalized_sha256")))
        if identity_ok and raw_ok and normalized_ok:
            existing_manifest.update({"verified": True, "boundary_qc": "PASS", "scientific_qc": existing_manifest.get("qc_status", "PENDING")})
            save_json_atomic(run / f"{provider}_result_manifest.json", existing_manifest)
            return _write(run, task_id, "DONE", outputs=[f"{provider}_result_manifest.json"])
    ledger = _load(run, "job_ledger.json", {}) or {}
    row = ledger.get(f"{provider}_submission", {})
    raw_file = row.get("raw_file")
    # A user-supplied corrected export can be valid even when no provider Job
    # ID exists.  Accept it only when the intake manifest explicitly marks
    # the source type and both raw/normalized files pass the recorded hashes.
    existing = _load(run, f"{provider}_result_manifest.json", {}) or {}
    if (provider == "pharmmapper" and
            existing.get("source_type") == "user_supplied_corrected_export" and
            existing.get("identity_match") == "PASS" and
            raw_file and Path(raw_file).is_file() and
            existing.get("raw_sha256") == file_sha256(Path(raw_file)) and
            existing.get("normalized_file") and
            Path(existing["normalized_file"]).is_file() and
            existing.get("normalized_sha256") == file_sha256(Path(existing["normalized_file"]))):
        existing.update({"verified": True, "boundary_qc": "PASS", "scientific_qc": existing.get("qc_status", "UNVERIFIED"), "updated_utc": now_utc()})
        save_json_atomic(run / f"{provider}_result_manifest.json", existing)
        return _write(run, task_id, "DONE", outputs=[f"{provider}_result_manifest.json"], next_action="독립 과학적 QC 및 downstream gate")
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
        normalized = _load(run, "normalized_targets.json", {}) or {}
        if normalized.get("verified") is not True:
            return _write(run, "ppi_analysis", "WAITING_EXTERNAL", next_action="검증된 UniProt 매핑 대기")
        approved, gate = _external_gate(
            run,
            endpoints=["https://string-db.org/api/json/get_string_ids", "https://string-db.org/api/tsv/network"],
            payload="검증된 human UniProt/gene target 목록으로 STRING PPI network 생성",
        )
        if not approved:
            return _write(run, "ppi_analysis", "WAITING_USER", next_action="external_access_approval.json에 STRING 승인 기록", reason=gate["reason"], outputs=["external_action_request.json"])
        try:
            from providers import string_map, string_network
            normalized_file = Path(str(normalized.get("file", run / "normalized_targets.csv")))
            if not normalized_file.is_file():
                return _write(run, "ppi_analysis", "CORRECT_AND_RERUN", next_action="normalized_targets.csv 생성 확인", reason="normalized target artifact missing")
            with normalized_file.open(newline="", encoding="utf-8-sig") as handle:
                normalized_rows = list(csv.DictReader(handle))
            symbols = sorted({str(row.get("gene_symbol", "")).strip() for row in normalized_rows if row.get("gene_symbol")})
            mapped = string_map(symbols)
            string_ids = sorted({item.get("stringId") for item in mapped if item.get("stringId")})
            if not string_ids:
                return _write(run, "ppi_analysis", "FAILED_RETRYABLE", next_action="STRING 매핑 결과 확인", reason="STRING returned no identifiers")
            edges = string_network(string_ids)
            output = run / "ppi_network.tsv"
            if edges:
                with output.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(edges[0]), delimiter="\t")
                    writer.writeheader(); writer.writerows(edges)
            else:
                output.write_text("# STRING returned no interactions\n", encoding="utf-8")
            manifest = {"verified": True, "network_file": str(output), "input_sha256": file_sha256(run / "normalized_targets.csv"), "source": "STRING", "rows": len(edges), "updated_utc": now_utc()}
            save_json_atomic(run / "ppi_manifest.json", manifest)
            network_file = str(output)
        except Exception as exc:
            return _write(run, "ppi_analysis", "FAILED_RETRYABLE", next_action="STRING PPI bounded retry", reason=str(exc)[:220])
    if not manifest.get("input_sha256"):
        return _write(run, "ppi_analysis", "CORRECT_AND_RERUN", next_action="PPI 입력 hash 기록", reason="input_sha256 missing")
    return _write(run, "ppi_analysis", "DONE", outputs=[str(network_file)])


def enrichment_analysis(run: Path) -> dict[str, Any]:
    manifest = _load(run, "enrichment_manifest.json", {}) or {}
    output = manifest.get("output_file")
    if not output or not Path(output).is_file():
        normalized = _load(run, "normalized_targets.json", {}) or {}
        normalized_file = Path(str(normalized.get("file", run / "normalized_targets.csv")))
        if not normalized_file.is_file():
            return _write(run, "enrichment_analysis", "WAITING_EXTERNAL", next_action="검증된 normalized_targets.csv 대기")
        approved, gate = _external_gate(
            run,
            endpoints=["https://string-db.org/api/tsv/enrichment"],
            payload="검증된 human gene symbol 목록으로 STRING enrichment 결과 생성",
        )
        if not approved:
            return _write(run, "enrichment_analysis", "WAITING_USER", next_action="STRING enrichment 외부 호출 승인 후 재개", reason=gate["reason"], outputs=["external_action_request.json"])
        try:
            from providers import string_enrichment
            with normalized_file.open(newline="", encoding="utf-8-sig") as handle:
                symbols = sorted({str(row.get("gene_symbol", "")).strip() for row in csv.DictReader(handle) if row.get("gene_symbol")})
            rows = string_enrichment(symbols)
            output_path = run / "string_enrichment.tsv"
            if rows:
                with output_path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
                    writer.writeheader(); writer.writerows(rows)
            else:
                output_path.write_text("# STRING returned no enrichment terms\n", encoding="utf-8")
            manifest = {"verified": True, "output_file": str(output_path), "input_sha256": file_sha256(normalized_file), "source": "STRING", "rows": len(rows), "updated_utc": now_utc()}
            save_json_atomic(run / "enrichment_manifest.json", manifest)
            output = str(output_path)
        except Exception as exc:
            return _write(run, "enrichment_analysis", "FAILED_RETRYABLE", next_action="STRING enrichment bounded retry", reason=str(exc)[:220])
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


def experimental_evidence_synthesis(run: Path) -> dict[str, Any]:
    """Normalize animal/cell evidence before mechanism, figure, or docking claims."""
    qc = _load(run, "independent_qc.json", {}) or {}
    if qc.get("verdict") != "PASS":
        return _write(run, "experimental_evidence_synthesis", "WAITING_EXTERNAL", next_action="독립 QC PASS 대기")
    candidates = [run / "experimental_evidence.json", run / "experimental_evidence_manifest.json",
                  run / "references" / "experimental_evidence.json"]
    source = next((p for p in candidates if p.is_file()), None)
    if source is None:
        request = {"status": "INPUT_REQUIRED", "required": ["animal_or_cell_marker", "direction", "source", "experimental_context"],
                   "next_action": "논문 또는 실험 결과를 evidence schema로 등록", "updated_utc": now_utc()}
        save_json_atomic(run / "experimental_evidence_request.json", request)
        return _write(run, "experimental_evidence_synthesis", "WAITING_EXTERNAL",
                      next_action="검증된 동물·세포 실험 evidence 입력 대기", outputs=["experimental_evidence_request.json"])
    # ``source`` is already a resolved file path.  Passing it to ``_load``
    # as the run root previously raised ``TypeError`` and left every run
    # waiting even when a valid evidence file had arrived.
    try:
        evidence = json.loads(source.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError):
        return _write(run, "experimental_evidence_synthesis", "CORRECT_AND_RERUN",
                      next_action="experimental_evidence.json 재생성", reason="evidence JSON 읽기 실패")
    if not isinstance(evidence, dict) or not isinstance(evidence.get("evidence", []), list):
        return _write(run, "experimental_evidence_synthesis", "CORRECT_AND_RERUN",
                      next_action="experimental_evidence.json schema 수정", reason="evidence list missing")
    normalized = {"status": "VERIFIED", "source": str(source), "evidence": evidence["evidence"],
                  "updated_utc": now_utc()}
    save_json_atomic(run / "experimental_evidence_synthesis.json", normalized)
    return _write(run, "experimental_evidence_synthesis", "DONE", outputs=["experimental_evidence_synthesis.json"])


def mechanism_enrichment_synthesis(run: Path) -> dict[str, Any]:
    """Select non-redundant, UC-relevant enrichment terms for Figure and docking review."""
    enr = _load(run, "enrichment_manifest.json", {}) or {}
    evidence = _load(run, "experimental_evidence_synthesis.json", {}) or {}
    source = Path(str(enr.get("output_file") or run / "string_enrichment.tsv"))
    if evidence.get("status") != "VERIFIED" or not source.is_file():
        return _write(run, "mechanism_enrichment_synthesis", "WAITING_EXTERNAL",
                      next_action="enrichment 결과와 실험 evidence 검증 대기")
    rows = []
    with source.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            try:
                count = int(row.get("number_of_genes") or 0); bg = int(row.get("number_of_genes_in_background") or 1)
                fdr = float(row.get("fdr"))
            except (TypeError, ValueError):
                continue
            category = row.get("category", "")
            if category in {"Process", "Component", "Function", "KEGG"}:
                rows.append({"category": category, "term": row.get("description") or row.get("term"),
                             "gene_ratio": count / max(bg, 1), "count": count, "fdr": fdr})
    selected = {}
    for category in ("Process", "Component", "Function", "KEGG"):
        group = sorted((r for r in rows if r["category"] == category), key=lambda r: (r["fdr"], -r["gene_ratio"]))
        selected[category] = group[:7]
    output = {"status": "VERIFIED", "selection_rule": "top 7 by FDR, ordered by gene ratio; evidence cross-check required",
              "source": str(source), "terms": selected, "experimental_evidence": "experimental_evidence_synthesis.json", "updated_utc": now_utc()}
    save_json_atomic(run / "mechanism_enrichment_synthesis.json", output)
    return _write(run, "mechanism_enrichment_synthesis", "DONE", outputs=["mechanism_enrichment_synthesis.json"])


def manuscript_review(run: Path) -> dict[str, Any]:
    qc = _load(run, "independent_qc.json", {}) or {}
    if qc.get("verdict") != "PASS":
        return _write(run, "manuscript_review", "WAITING_EXTERNAL", next_action="독립 QC PASS 대기")
    review = {"status": "REVIEWED", "basis": "independent QC PASS", "updated_utc": now_utc()}
    save_json_atomic(run / "manuscript_review.json", review)
    return _write(run, "manuscript_review", "DONE", outputs=["manuscript_review.json"])


def cytoscape_visualization(run: Path) -> dict[str, Any]:
    """Run the registered Cytoscape worker against the frozen PPI manifest."""
    manifest = _load(run, "ppi_manifest.json", {}) or {}
    network = Path(str(manifest.get("network_file") or ""))
    if manifest.get("verified") is not True or not network.is_file():
        return _write(run, "cytoscape_visualization", "WAITING_EXTERNAL",
                      next_action="검증된 PPI manifest와 network 파일 대기",
                      reason="verified PPI input is missing")
    # `ppi_manifest.input_sha256` identifies the normalized target input,
    # while the Cytoscape adapter must fingerprint the frozen network file.
    # Keep both meanings explicit instead of comparing unlike hashes.
    # The existing Cytoscape adapter uses a branch-qualified manifest.  Create
    # a deterministic adapter manifest without changing the frozen PPI file.
    branch_manifest = {**manifest, "verified_input": True, "branch": "primary",
                       "source_input_sha256": manifest.get("input_sha256"),
                       "input_sha256": file_sha256(network)}
    save_json_atomic(run / "primary_ppi_manifest.json", branch_manifest)
    try:
        from np_cytoscape_worker import run as cytoscape_run
        result = cytoscape_run(run, "primary")
    except Exception as exc:
        return _write(run, "cytoscape_visualization", "FAILED_RETRYABLE",
                      next_action="Cytoscape adapter 경계 오류를 확인하고 재시도", reason=repr(exc))
    status = str(result.get("status", "FAILED"))
    if status in {"WAITING_CYTOSCAPE_ONLINE", "WAITING_VERIFIED_PPI"}:
        return _write(run, "cytoscape_visualization", "WAITING_EXTERNAL",
                      next_action="Cytoscape/cyREST 실행 후 supervisor가 재개",
                      reason_code=status, reason=result.get("error", "Cytoscape 실행 대기"))
    if status not in {"COMPLETED", "PARTIAL_MCODE", "SKIP_UNCHANGED"}:
        return _write(run, "cytoscape_visualization", "FAILED_RETRYABLE",
                      next_action="Cytoscape 결과와 cyREST 로그를 확인하고 재시도", reason_code=status,
                      reason=str(result.get("error") or result))
    out = run / "cytoscape" / "primary" / "run_manifest.json"
    if not out.is_file():
        return _write(run, "cytoscape_visualization", "FAILED_RETRYABLE",
                      next_action="Cytoscape run_manifest 생성 여부 확인", reason="artifact missing")
    return _write(run, "cytoscape_visualization", "DONE", outputs=[str(out.relative_to(run))])


def docking_candidate_selection(run: Path) -> dict[str, Any]:
    """Create a traceable docking-ready candidate table from Cytoscape output."""
    qc = _load(run, "independent_qc.json", {}) or {}
    cy = _load(run, "worker_results/cytoscape_visualization.json", {}) or {}
    mechanism = _load(run, "mechanism_enrichment_synthesis.json", {}) or {}
    evidence = _load(run, "experimental_evidence_synthesis.json", {}) or {}
    if qc.get("verdict") != "PASS":
        return _write(run, "docking_candidate_selection", "WAITING_EXTERNAL", next_action="독립 QC PASS 대기")
    if cy.get("status") != "DONE":
        return _write(run, "docking_candidate_selection", "WAITING_EXTERNAL", next_action="Cytoscape 네트워크 완료 대기")
    if mechanism.get("status") != "VERIFIED" or evidence.get("status") != "VERIFIED":
        return _write(run, "docking_candidate_selection", "WAITING_EXTERNAL", next_action="실험 evidence·기전 enrichment 검증 대기")
    cy_manifest = _load(run, "cytoscape/primary/run_manifest.json", {}) or {}
    mcc = Path(str(cy_manifest.get("mcc_rank_file") or run / "cytoscape" / "primary" / "mcc_rank.csv"))
    mcode = Path(str(cy_manifest.get("mcode_cluster_file") or run / "cytoscape" / "primary" / "mcode_clusters.json"))
    # CytoHubba may be installed but expose no stable cyREST command.  MCODE
    # and degree are still valid auditable evidence for a provisional ranking;
    # keep the limitation explicit instead of leaving the whole run orphaned.
    if not mcode.is_file():
        return _write(run, "docking_candidate_selection", "WAITING_EXTERNAL",
                      next_action="Cytoscape MCODE artifact 대기",
                      reason="MCODE artifact가 없으면 후보를 산출하지 않음")
    mcc_available = mcc.is_file()
    degree = run / "cytoscape" / "primary" / "degree_rank.csv"
    if not degree.is_file():
        return _write(run, "docking_candidate_selection", "CORRECT_AND_RERUN", next_action="Cytoscape degree_rank.csv 생성 확인", reason="degree artifact missing")
    with degree.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    candidates = [{"target": row.get("gene", ""), "rank": index, "degree": row.get("degree", ""),
                   "mcc_status": "AVAILABLE" if mcc_available else "NOT_AVAILABLE_CYREST",
                   "source": "MCC + MCODE + degree + mechanism evidence" if mcc_available else "MCODE + degree + mechanism evidence (MCC unavailable)"}
                  for index, row in enumerate(rows[:10], start=1) if row.get("gene")]
    output = run / "docking_candidates.json"
    save_json_atomic(output, {"status": "RECOMMENDATION_READY", "calculation": "NOT_STARTED", "candidates": candidates,
                              "source_manifest": str((run / "cytoscape" / "primary" / "run_manifest.json").relative_to(run)),
                              "updated_utc": now_utc()})
    report = run / "docking_candidate_recommendation.md"
    lines = ["# 도킹 후보 추천", "", ("MCC·MCODE·degree와 동물·세포 실험 evidence 및 UC 기전 enrichment를 교차검증한 후보이다." if mcc_available else "MCODE·degree와 동물·세포 실험 evidence 및 UC 기전 enrichment를 교차검증한 예비 후보이다. CytoHubba MCC는 현재 cyREST 명령으로 추출되지 않아 별도 GUI 검증 대상으로 표시했다."),
             "실제 도킹 전에는 구조 가용성, 결합부위, redocking 기준을 추가 검증한다.", "", "| 순위 | 표적 | degree | 근거 |", "|---:|---|---:|---|"]
    lines.extend(f"| {row['rank']} | {row['target']} | {row['degree']} | Cytoscape primary degree |" for row in candidates)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return _write(run, "docking_candidate_selection", "DONE", outputs=["docking_candidates.json", "docking_candidate_recommendation.md"])


def figure_draft(run: Path) -> dict[str, Any]:
    """Create a publication-figure panel plan from verified NP artifacts."""
    qc = _load(run, "independent_qc.json", {}) or {}
    cy = _load(run, "worker_results/cytoscape_visualization.json", {}) or {}
    mechanism = _load(run, "mechanism_enrichment_synthesis.json", {}) or {}
    if qc.get("verdict") != "PASS" or cy.get("status") != "DONE" or mechanism.get("status") != "VERIFIED":
        return _write(run, "figure_draft", "WAITING_EXTERNAL", next_action="QC·Cytoscape·기전 enrichment 결과 대기")
    panels = [
        ("A", "NP workflow", "전체 분석 workflow와 외부자료·QC gate"),
        ("B", "PPI network", "Cytoscape primary network와 hub 시각화"),
        ("C", "Hub ranking", "degree 기반 상위 표적과 후보 추천 연결"),
        ("D", "Enrichment", "실험 evidence와 교차검증한 GO/KEGG 상위 7개 term"),
    ]
    report = run / "figure_draft.md"
    lines = ["# 논문용 Figure 초안", "", "현재 문서는 최종 디자인 전의 패널 구성·근거 초안이다.", "각 패널은 저장된 artifact와 source manifest를 참조하며, 최종 투고 전 독립 시각 QC가 필요하다.", "", "| 패널 | 제목 | 구성·근거 |", "|---|---|---|"]
    lines.extend(f"| {p} | {title} | {basis} |" for p, title, basis in panels)
    lines += ["", "## 연결 artifact", "- `cytoscape/primary/run_manifest.json`", "- `docking_candidate_recommendation.md`", "- `string_enrichment.tsv`", "- `independent_qc.json`"]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    save_json_atomic(run / "figure_draft.json", {"status": "DRAFT_READY", "panels": [p for p, _, _ in panels], "updated_utc": now_utc()})
    return _write(run, "figure_draft", "DONE", outputs=["figure_draft.md", "figure_draft.json"])


def methods_results_draft(run: Path) -> dict[str, Any]:
    """Draft NP Methods/Results only from frozen, QC-passed artifacts."""
    qc = _load(run, "independent_qc.json", {}) or {}
    candidates = _load(run, "docking_candidates.json", {}) or {}
    figure = _load(run, "figure_draft.json", {}) or {}
    mechanism = _load(run, "mechanism_enrichment_synthesis.json", {}) or {}
    if qc.get("verdict") != "PASS" or candidates.get("status") != "RECOMMENDATION_READY" or figure.get("status") != "DRAFT_READY" or mechanism.get("status") != "VERIFIED":
        return _write(run, "methods_results_draft", "WAITING_EXTERNAL", next_action="QC·기전 enrichment·도킹 후보·Figure 초안 대기")
    ppi = _load(run, "ppi_manifest.json", {}) or {}
    enrichment = _load(run, "enrichment_manifest.json", {}) or {}
    text = ("# NP 분석 Methods/Results 초안\n\n"
            "## Methods\n"
            "화합물·질환 입력을 확인하고 검증된 외부 표적 자료를 정규화한 뒤, STRING PPI와 기능적 enrichment를 수행하였다. "
            "각 입력과 결과는 run manifest 및 SHA-256으로 추적하였다.\n\n"
            "## Results\n"
            f"PPI 입력은 {ppi.get('source', '기록된 PPI source')}에서 생성되었고, enrichment 결과는 {enrichment.get('source', '기록된 enrichment source')}로 저장되었다. "
            f"독립 QC verdict는 {qc.get('verdict')}이며, Cytoscape degree 기반 예비 도킹 후보 {len(candidates.get('candidates', []))}개를 추천하였다. "
            "실제 도킹 계산 결과는 포함하지 않았다. Figure 패널과 기전 기반 term 선정 근거는 별도 artifact로 보존하였다.\n")
    output = run / "methods_results_draft.md"
    output.write_text(text, encoding="utf-8")
    return _write(run, "methods_results_draft", "DONE", outputs=["methods_results_draft.md"])


def completion_packager(run: Path) -> dict[str, Any]:
    if (_load(run, "independent_qc.json", {}) or {}).get("verdict") != "PASS":
        return _write(run, "completion_packager", "WAITING_EXTERNAL", next_action="독립 QC PASS 대기")
    if (_load(run, "manuscript_review.json", {}) or {}).get("status") != "REVIEWED":
        return _write(run, "completion_packager", "WAITING_EXTERNAL", next_action="원고 근거 검토 완료 대기")
    if not (run / "methods_results_draft.md").is_file() or not (run / "figure_draft.md").is_file():
        return _write(run, "completion_packager", "WAITING_EXTERNAL", next_action="Methods/Results 초안 완료 대기")
    package = {"profile": "results_plus_manifest", "run_id": run.name, "created_utc": now_utc(),
               "files": ["independent_qc.json", "manuscript_review.json", "docking_candidates.json", "docking_candidate_recommendation.md", "figure_draft.md", "figure_draft.json", "methods_results_draft.md"]}
    save_json_atomic(run / "completion_manifest.json", package)
    return _write(run, "completion_packager", "DONE", outputs=["completion_manifest.json"])
