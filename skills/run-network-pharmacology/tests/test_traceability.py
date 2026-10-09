"""Contract-v7 traceability tests for the reusable NP skill."""

import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import unittest


class _NoopMark:
    def parametrize(self, *_args, **_kwargs):
        return lambda function: function


class _NoopPytest:
    mark = _NoopMark()

    @staticmethod
    def skip(message):
        raise unittest.SkipTest(message)


pytest = _NoopPytest()

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from traceability import validate_traceability  # noqa: E402


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_valid_run(tmp_path):
    root = tmp_path / "run"
    for name in ("source_archive", "raw", "normalized", "scripts"):
        (root / name).mkdir(parents=True)
    archive = root / "source_archive" / "sea.json"
    archive.write_text('{"targets": []}\n', encoding="utf-8")
    raw = root / "raw" / "sea.json"
    raw.write_bytes(archive.read_bytes())
    normalized = root / "normalized" / "targets.csv"
    normalized.write_text("gene_symbol\n", encoding="utf-8")
    script = root / "scripts" / "normalize.py"
    script.write_text("# normalization used for this run\n", encoding="utf-8")
    write_csv(root / "source_archive_index.csv", ["artifact_id", "archive_path", "sha256", "bytes", "redaction_note"], [{"artifact_id": "arc-1", "archive_path": "source_archive/sea.json", "sha256": sha256(archive), "bytes": archive.stat().st_size, "redaction_note": "none"}])
    fields = ["attempt_id", "subject_type", "subject_id", "provider", "source_role", "query", "status", "retrieval_status", "evidence_status", "source_url", "job_id", "collected_utc", "native_score_rank_meaning", "provider_version", "provenance_status", "provenance_reason", "pagination_required", "pagination_complete", "retrieval_complete", "pagination_end_evidence", "final_artifact_id", "constituent_scope"]
    row = {"attempt_id": "a-1", "subject_type": "compound", "subject_id": "CHEMBL:1", "provider": "SEA", "source_role": "source_panel", "query": "CCO", "status": "retrieved", "retrieval_status": "retrieved", "evidence_status": "primary_eligible", "source_url": "https://example.test/sea", "job_id": "NOT_APPLICABLE", "collected_utc": "2026-10-09T00:00:00Z", "native_score_rank_meaning": "p-value", "provider_version": "v1", "provenance_status": "VERIFIED", "provenance_reason": "NOT_APPLICABLE", "pagination_required": "false", "pagination_complete": "NOT_APPLICABLE", "retrieval_complete": "true", "pagination_end_evidence": "NOT_APPLICABLE", "final_artifact_id": "arc-1", "constituent_scope": "NOT_APPLICABLE"}
    write_csv(root / "source_attempts.csv", fields, [row])
    adapter_fields = ["adapter_run_id", "attempt_id", "adapter", "adapter_version", "query", "raw_response_paths", "raw_response_sha256", "output_paths", "output_sha256"]
    write_csv(root / "data_adapter_ledger.csv", adapter_fields, [])
    lineage_fields = ["lineage_id", "output_path", "output_sha256", "input_paths", "input_sha256", "transformation_type", "transformation_script_path", "transformation_script_sha256", "tool", "tool_version", "work_record"]
    lineage_rows = [
        {"lineage_id": "l-1", "output_path": "raw/sea.json", "output_sha256": sha256(raw), "input_paths": json.dumps(["source_archive/sea.json"]), "input_sha256": json.dumps([sha256(archive)]), "transformation_type": "copy", "transformation_script_path": "scripts/normalize.py", "transformation_script_sha256": sha256(script), "tool": "python", "tool_version": "3", "work_record": "copy"},
        {"lineage_id": "l-2", "output_path": "normalized/targets.csv", "output_sha256": sha256(normalized), "input_paths": json.dumps(["raw/sea.json"]), "input_sha256": json.dumps([sha256(raw)]), "transformation_type": "manual", "transformation_script_path": "NOT_APPLICABLE", "transformation_script_sha256": "NOT_APPLICABLE", "tool": "spreadsheet", "tool_version": "1", "work_record": "manual normalization recorded"},
    ]
    write_csv(root / "data_lineage.csv", lineage_fields, lineage_rows)
    manifest = {"contract_version": 7, "source_archive_policy_version": 2, "subjects": [{"subject_type": "compound", "subject_id": "CHEMBL:1"}], "required_source_attempts": [{"subject_type": "compound", "subject_id": "CHEMBL:1", "provider": "SEA", "source_role": "source_panel"}], "used_adapters": [], "files": ["source_attempts.csv", "source_archive_index.csv", "data_adapter_ledger.csv", "data_lineage.csv"]}
    return root, manifest


class TraceabilityTests(unittest.TestCase):
    def test_valid_v7_traceability_accepts_manual_transform_and_empty_retrieval(self):
        with tempfile.TemporaryDirectory() as temp:
            root, manifest = make_valid_run(Path(temp))
            self.assertEqual(validate_traceability(root, manifest), [])


@pytest.mark.parametrize("mutator, expected", [(lambda root: (root / "source_archive" / "sea.json").unlink(), "missing archive"), (lambda root: (root / "source_archive" / "sea.json").write_text("tampered", encoding="utf-8"), "sha256")])
def test_archive_integrity_failures_are_rejected(valid_run, mutator, expected):
    root, manifest = valid_run
    mutator(root)
    assert expected in "\n".join(validate_traceability(root, manifest))


def test_duplicate_archive_index_and_incomplete_pagination_are_rejected(valid_run):
    root, manifest = valid_run
    path = root / "source_archive_index.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    write_csv(path, rows[0].keys(), rows + rows)
    path = root / "source_attempts.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    rows[0].update({"pagination_required": "true", "pagination_complete": "false", "retrieval_complete": "false", "pagination_end_evidence": "preview only"})
    write_csv(path, rows[0].keys(), rows)
    problems = "\n".join(validate_traceability(root, manifest))
    assert "duplicate artifact_id" in problems and "pagination is incomplete" in problems


def test_missing_required_attempt_and_adapter_ledger_are_rejected(valid_run):
    root, manifest = valid_run
    manifest["required_source_attempts"].append({"subject_type": "disease_ontology", "subject_id": "MONDO:1", "provider": "GeneCards", "source_role": "source_panel"})
    manifest["used_adapters"] = ["ChEMBL"]
    (root / "data_adapter_ledger.csv").unlink()
    problems = "\n".join(validate_traceability(root, manifest))
    assert "missing required source attempt" in problems and "missing: data_adapter_ledger.csv" in problems


def test_lineage_duplicate_and_cycle_are_rejected(valid_run):
    root, manifest = valid_run
    path = root / "data_lineage.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    rows.append(dict(rows[1]))
    rows[0]["input_paths"] = json.dumps(["normalized/targets.csv"])
    rows[0]["input_sha256"] = json.dumps([sha256(root / "normalized" / "targets.csv")])
    write_csv(path, rows[0].keys(), rows)
    problems = "\n".join(validate_traceability(root, manifest))
    assert "duplicate output_path" in problems and "cycle" in problems


def test_manifest_builder_inventory_and_external_symlink_are_checked(valid_run):
    root, manifest = valid_run
    seed = root / "seed.json"
    seed.write_text(json.dumps(manifest), encoding="utf-8")
    output = root / "NP_manifest.json"
    completed = subprocess.run([sys.executable, str(SCRIPTS / "build_manifest.py"), str(root), str(seed), str(output)], capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    generated = json.loads(output.read_text(encoding="utf-8"))
    assert all(item["path"] != "NP_manifest.json" for item in generated["file_inventory"])
    external = root.parent / "outside.txt"
    external.write_text("outside", encoding="utf-8")
    link = root / "raw" / "outside-link.txt"
    try:
        os.symlink(external, link)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink unavailable: {exc}")
    failed = subprocess.run([sys.executable, str(SCRIPTS / "build_manifest.py"), str(root), str(seed), str(output)], capture_output=True, text=True)
    assert failed.returncode != 0 and "symlink" in failed.stderr.casefold()
