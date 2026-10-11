import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import np_agent_queue
import np_harness
import np_workers


class NpPipelineTailTests(unittest.TestCase):
    def test_new_queue_contains_visualization_docking_and_manuscript_draft_tail(self):
        with tempfile.TemporaryDirectory() as temp:
            run = np_agent_queue.initialize(Path(temp), "A CID 1", "disease X", "Homo sapiens")
            queue = json.loads((run / "work_queue.json").read_text(encoding="utf-8"))
            tasks = {item["id"]: item for item in queue["tasks"]}
            self.assertEqual(tasks["cytoscape_visualization"]["requires"], ["final_ppi", "independent_qc"])
            self.assertEqual(tasks["docking_candidate_selection"]["requires"], [
                "cytoscape_visualization", "mechanism_enrichment_synthesis", "experimental_evidence_synthesis", "figure_draft"
            ])
            self.assertEqual(tasks["methods_results_draft"]["requires"], [
                "docking_candidate_selection", "figure_draft", "mechanism_enrichment_synthesis"
            ])
            self.assertEqual(tasks["completion_packager"]["requires"], ["manuscript_review", "methods_results_draft", "figure_draft"])

    def test_validate_requires_pipeline_tail(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "request.json").write_text(json.dumps({"compound_input": "A", "disease_input": "X", "species": "human"}), encoding="utf-8")
            tasks = [{"id": key, "status": "DONE", "requires": []} for key in (
                "independent_qc", "manuscript_review", "cytoscape_visualization",
                "docking_candidate_selection", "methods_results_draft")]
            (run / "work_queue.json").write_text(json.dumps({"tasks": tasks}), encoding="utf-8")
            result = np_harness.validate_run(run)
            self.assertEqual(result["status"], "IN_PROGRESS")
            self.assertIn("completion_packager", result["unfinished"])

    def test_cytoscape_worker_reports_waiting_when_service_is_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            ppi = run / "ppi_network.tsv"
            ppi.write_text("preferredName_A\tpreferredName_B\nA\tB\n", encoding="utf-8")
            manifest = {"verified": True, "verified_input": True, "branch": "primary", "network_file": str(ppi), "input_sha256": np_workers.file_sha256(ppi)}
            (run / "ppi_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            # Keep this regression test deterministic even when a local
            # Cytoscape instance is running for an active analysis.
            with patch("np_cytoscape_worker.run", return_value={
                "status": "WAITING_CYTOSCAPE_ONLINE",
                "error": "test offline dependency",
            }):
                result = np_workers.cytoscape_visualization(run)
            self.assertEqual(result["status"], "WAITING_EXTERNAL")
            self.assertEqual(result["reason_code"], "WAITING_CYTOSCAPE_ONLINE")


if __name__ == "__main__":
    unittest.main()
