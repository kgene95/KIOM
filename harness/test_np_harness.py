import json
import tempfile
import unittest
from pathlib import Path

from np_harness import build_plan, cycle, validate_run

class HarnessTests(unittest.TestCase):
    def test_parallel_plan_keeps_independent_tasks_together(self):
        queue = {"tasks": [
            {"id": "identity", "agent": "agent1", "requires": [], "status": "DONE"},
            {"id": "disease_targets", "agent": "agent1", "requires": [], "status": "DONE"},
            {"id": "structure_handoff", "agent": "agent1", "requires": ["identity"], "status": "DONE"},
            {"id": "initial_ppi", "agent": "agent3", "requires": ["disease_targets"], "status": "QUEUED"},
            {"id": "sea_submission", "agent": "agent2", "requires": ["structure_handoff"], "status": "QUEUED"},
        ]}
        plan = build_plan(queue, 1)
        ids = {item["id"] for group in plan["parallel_groups"] for item in group}
        self.assertEqual(ids, {"initial_ppi", "sea_submission"})

    def test_cycle_persists_waiting_gate_and_plan(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "request.json").write_text(json.dumps({"run_id": "t"}), encoding="utf-8")
            (run / "work_queue.json").write_text(json.dumps({"tasks": [
                {"id": "identity", "agent": "agent1", "requires": [], "status": "DONE"},
                {"id": "source_reuse_decision", "agent": "controller", "requires": ["identity"], "status": "QUEUED"},
            ]}), encoding="utf-8")
            state = cycle(run, dry_run=False, max_cycles=1)
            queue = json.loads((run / "work_queue.json").read_text(encoding="utf-8"))
            self.assertEqual(queue["tasks"][1]["status"], "WAITING_USER")
            self.assertTrue((run / "dispatch_plan.json").exists())
            self.assertEqual(state["status"], "WAITING")

    def test_cycle_budget_stops_without_looping(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "work_queue.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
            cycle(run, dry_run=True, max_cycles=1)
            state = cycle(run, dry_run=True, max_cycles=1)
            self.assertEqual(state["status"], "BUDGET_STOP")

    def test_validate_reports_waiting_gate_without_claiming_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "request.json").write_text(json.dumps({
                "compound_input": "CID 1", "disease_input": "colitis", "species": "Homo sapiens"
            }), encoding="utf-8")
            (run / "work_queue.json").write_text(json.dumps({"tasks": [
                {"id": "independent_qc", "status": "WAITING_EXTERNAL"},
                {"id": "manuscript_review", "status": "QUEUED"}
            ]}), encoding="utf-8")
            result = validate_run(run)
            self.assertEqual(result["status"], "WAITING")
            self.assertTrue((run / "np_validation.json").exists())

if __name__ == "__main__":
    unittest.main()
