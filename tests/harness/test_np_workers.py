import json
import tempfile
import unittest
from pathlib import Path

from harness.dispatcher import dispatch_registered_worker
from harness.np_workers import (compound_identity, source_audit, structure_qc,
                                 independent_qc, integration_analysis, manuscript_review)


ROOT = Path(__file__).parents[2]


class NPWorkerTests(unittest.TestCase):
    def test_identity_worker_creates_result(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "request.json").write_text(json.dumps({
                "compound_input": "CID 439246", "disease_input": "colitis", "species": "Homo sapiens"
            }), encoding="utf-8")
            result = compound_identity(run)
            self.assertEqual(result["status"], "DONE")
            self.assertTrue((run / "worker_results/compound_identity.json").exists())

    def test_source_audit_requires_explicit_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            result = source_audit(run)
            self.assertEqual(result["status"], "WAITING_USER")

    def test_dispatcher_rejects_unregistered_or_runs_registered_local_worker(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "request.json").write_text(json.dumps({
                "compound_input": "CID 1", "disease_input": "colitis", "species": "Homo sapiens"
            }), encoding="utf-8")
            registry = ROOT / "harness/worker_registry.json"
            result = dispatch_registered_worker(run, {"id": "compound_identity", "worker": "compound_identity"}, registry)
            self.assertEqual(result["status"], "DONE")
            missing = dispatch_registered_worker(run, {"id": "x", "worker": "does_not_exist"}, registry)
            self.assertEqual(missing["status"], "FAILED")

    def test_analysis_chain_requires_gates_and_then_produces_qc(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            self.assertEqual(integration_analysis(run)["status"], "WAITING_EXTERNAL")
            for name in ("overlap_analysis", "ppi_analysis", "enrichment_analysis"):
                (run / "worker_results").mkdir(exist_ok=True)
                (run / "worker_results" / f"{name}.json").write_text(json.dumps({"status": "DONE"}), encoding="utf-8")
            self.assertEqual(integration_analysis(run)["status"], "DONE")
            self.assertEqual(independent_qc(run)["status"], "DONE")
            self.assertEqual(manuscript_review(run)["status"], "DONE")


if __name__ == "__main__":
    unittest.main()
