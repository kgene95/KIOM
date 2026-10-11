import json
import sys
import tempfile
import unittest
from pathlib import Path

from np_harness import build_plan, cycle, ingest_external_events, read, reconcile_queue, validate_run

SCRIPTS = Path(__file__).parents[1] / "skills" / "run-network-pharmacology" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import np_agent_queue

class HarnessTests(unittest.TestCase):
    def test_external_upload_is_hashed_and_recorded_once(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp); incoming = run / "incoming"; incoming.mkdir()
            upload = incoming / "pharmmapper_test.csv"; upload.write_text("Ligand: 1\n", encoding="utf-8")
            first = ingest_external_events(run)
            second = ingest_external_events(run)
            self.assertEqual(len(first), 1)
            self.assertEqual(first[0]["provider"], "pharmmapper")
            self.assertEqual(second, [])
            self.assertTrue((run / "external_event_manifest.json").exists())
            self.assertIn('"event_type": "EXTERNAL_DATA_RECEIVED"', (run / "event_log.jsonl").read_text(encoding="utf-8"))

    def test_queue_sync_accepts_utf8_bom_json_written_by_powershell(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "work_queue.json"
            path.write_text(json.dumps({"tasks": []}), encoding="utf-8-sig")
            self.assertEqual(np_agent_queue.load(path, {}).get("tasks"), [])
            self.assertEqual(read(path, {}).get("tasks"), [])

    def test_reconcile_repairs_completed_provider_tasks_from_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            sea_raw = run / "sea.zip"
            pm_raw = run / "pharmmapper.csv"
            sea_raw.write_bytes(b"PK-test")
            pm_raw.write_text("Ligand: 1\n", encoding="utf-8")
            (run / "job_ledger.json").write_text(json.dumps({
                "sea_submission": {"status": "RETRIEVED_UNVERIFIED", "job_id": "sea-1", "cid": "1", "input_sha256": "s", "raw_file": str(sea_raw)},
                "pharmmapper_submission": {"status": "RESULT_FILE_RECEIVED_UNVERIFIED", "job_id": "pm-1", "cid": "1", "input_sha256": "s", "result_file": str(pm_raw)},
            }), encoding="utf-8")
            queue = {"tasks": [
                {"id": "sea_submission", "status": "NEEDS_EXTERNAL_SUBMISSION", "requires": []},
                {"id": "sea_collect", "status": "QUEUED", "requires": ["sea_submission"]},
                {"id": "pharmmapper_submission", "status": "NEEDS_EXTERNAL_SUBMISSION", "requires": []},
                {"id": "pharmmapper_collect", "status": "QUEUED", "requires": ["pharmmapper_submission"]},
            ]}
            repaired = reconcile_queue(run, queue)
            statuses = {task["id"]: task["status"] for task in repaired["tasks"]}
            self.assertEqual(statuses["sea_submission"], "DONE")
            self.assertEqual(statuses["sea_collect"], "DONE_RAW_UNVERIFIED")
            self.assertEqual(statuses["pharmmapper_submission"], "DONE")
            self.assertEqual(statuses["pharmmapper_collect"], "DONE_RAW_UNVERIFIED")

    def test_reconcile_blocks_provider_cid_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "job_ledger.json").write_text(json.dumps({
                "pharmmapper_submission": {"status": "RESULT_FILE_RECEIVED_UNVERIFIED", "job_id": "pm-1", "cid": "56776173"},
            }), encoding="utf-8")
            queue = {"tasks": [{"id": "pharmmapper_submission", "status": "DONE", "requires": []}]}
            repaired = reconcile_queue(run, queue, expected_cid="75596314")
            self.assertEqual(repaired["tasks"][0]["status"], "IDENTITY_MISMATCH")

    def test_external_gate_wakes_failed_worker_after_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            queue = {"tasks": [{"id": "initial_ppi", "status": "FAILED", "requires": []}]}
            (run / "external_action_request.json").write_text(json.dumps({"status": "WAITING_USER"}), encoding="utf-8")
            (run / "external_access_approval.json").write_text(json.dumps({"approved": True}), encoding="utf-8")
            result = reconcile_queue(run, queue)
            self.assertEqual(result["tasks"][0]["status"], "READY_FOR_WORKER")

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

    def test_cycle_reconciles_provider_completion_before_dispatch(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            raw = run / "result.csv"
            raw.write_text("Ligand: 1\n", encoding="utf-8")
            (run / "request.json").write_text(json.dumps({"run_id": "t"}), encoding="utf-8")
            (run / "structure_manifest.json").write_text(json.dumps({"cid": "1"}), encoding="utf-8")
            (run / "job_ledger.json").write_text(json.dumps({
                "pharmmapper_submission": {"status": "RESULT_FILE_RECEIVED_UNVERIFIED", "job_id": "pm-1", "cid": "1", "result_file": str(raw)},
            }), encoding="utf-8")
            (run / "work_queue.json").write_text(json.dumps({"tasks": [
                {"id": "pharmmapper_submission", "agent": "agent2", "requires": [], "status": "NEEDS_EXTERNAL_SUBMISSION"},
                {"id": "pharmmapper_collect", "agent": "agent2", "requires": ["pharmmapper_submission"], "status": "QUEUED"},
            ]}), encoding="utf-8")
            cycle(run, dry_run=False, max_cycles=1)
            queue = json.loads((run / "work_queue.json").read_text(encoding="utf-8"))
            statuses = {task["id"]: task["status"] for task in queue["tasks"]}
            self.assertEqual(statuses["pharmmapper_submission"], "DONE")
            self.assertEqual(statuses["pharmmapper_collect"], "DONE_RAW_UNVERIFIED")

    def test_cycle_budget_stops_without_looping(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "work_queue.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
            cycle(run, dry_run=True, max_cycles=1)
            state = cycle(run, dry_run=True, max_cycles=1)
            self.assertEqual(state["status"], "BUDGET_STOP")

    def test_successful_cycle_clears_stale_error(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "request.json").write_text(json.dumps({"run_id": "t"}), encoding="utf-8")
            (run / "harness_state.json").write_text(json.dumps({"run_id": "t", "cycle": 0, "max_cycles": 10, "last_error": "old"}), encoding="utf-8")
            (run / "work_queue.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
            state = cycle(run, dry_run=True, max_cycles=10)
            self.assertNotIn("last_error", state)

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
