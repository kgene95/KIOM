import json
import tempfile
import unittest
from pathlib import Path

from harness.dispatcher import dispatch_registered_worker
from harness.np_workers import (compound_identity, source_audit, structure_qc,
                                 independent_qc, integration_analysis, manuscript_review,
                                 initial_ppi, ppi_analysis, external_data_intake)
from harness.event_agent import route_external_events


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

    def test_external_mapping_creates_explicit_gate_instead_of_retry_loop(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "compound_targets.csv").write_text(
                "compound_cid,target_id,target_name,source,source_score\n439246,CAH2,Carbonic anhydrase 2,PharmMapper,0.9\n",
                encoding="utf-8",
            )
            result = initial_ppi(run)
            self.assertEqual(result["status"], "WAITING_USER")
            request = json.loads((run / "external_action_request.json").read_text(encoding="utf-8"))
            self.assertIn("rest.uniprot.org", request["endpoints"][0])

    def test_ppi_analysis_requires_string_gate_after_verified_mapping(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "normalized_targets.json").write_text(json.dumps({
                "verified": True, "rows": [{"gene_symbol": "CA2"}]
            }), encoding="utf-8")
            result = ppi_analysis(run)
            self.assertEqual(result["status"], "WAITING_USER")
            request = json.loads((run / "external_action_request.json").read_text(encoding="utf-8"))
            self.assertTrue(any("string-db.org" in endpoint for endpoint in request["endpoints"]))

    def test_external_intake_archives_and_notifies_domain_worker(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "request.json").write_text(json.dumps({"compound_cid": "439246"}), encoding="utf-8")
            incoming = run / "incoming"; incoming.mkdir()
            (incoming / "pharmmapper_CID439246.csv").write_text("Ligand,target\n439246,CAH2\n", encoding="utf-8")
            result = external_data_intake(run)
            self.assertEqual(result["status"], "DONE")
            self.assertTrue((run / "source_archive/ExternalIntake/pharmmapper_CID439246.csv").exists())
            self.assertIn("pharmmapper_collect", (run / "worker_notifications.jsonl").read_text(encoding="utf-8"))

    def test_event_agent_routes_validated_external_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "request.json").write_text(json.dumps({"compound_cid": "439246"}), encoding="utf-8")
            incoming = run / "incoming"; incoming.mkdir()
            (incoming / "pharmmapper_CID439246.csv").write_text("Ligand,target\n439246,CAH2\n", encoding="utf-8")
            result = route_external_events(run)
            self.assertEqual(result["status"], "DONE")
            self.assertEqual(result["routes"][0]["recipient_worker"], "pharmmapper_collect")
            self.assertTrue((run / "event_agent_report.json").exists())


if __name__ == "__main__":
    unittest.main()
