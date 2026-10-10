import json
import tempfile
import unittest
from pathlib import Path

from harness.recovery import classify_error
from harness.state_store import append_event, load_json, update_state
from harness.verifier import verify_artifacts, verify_run_contract


class RuntimeContractTests(unittest.TestCase):
    def test_state_and_event_are_persistent(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            state = update_state(run, status="WAITING_EXTERNAL", next_action="check provider")
            append_event(run, {"event": "state_changed", "status": state["status"]})
            self.assertEqual(load_json(run / "harness_state.json", {})["status"], "WAITING_EXTERNAL")
            self.assertEqual(len((run / "event_log.jsonl").read_text(encoding="utf-8").splitlines()), 1)

    def test_recovery_is_bounded(self):
        self.assertEqual(classify_error("provider timeout", 0).status, "FAILED_RETRYABLE")
        self.assertEqual(classify_error("provider timeout", 3).status, "BUDGET_STOP")
        self.assertEqual(classify_error("approval required", 0).status, "WAITING_USER")

    def test_artifact_hash_and_run_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            for name, value in (("request.json", "{}"), ("work_queue.json", '{"tasks": []}'), ("harness_state.json", '{}')):
                (run / name).write_text(value, encoding="utf-8")
            output = run / "result.txt"
            output.write_text("ok", encoding="utf-8")
            import hashlib
            sha = hashlib.sha256(b"ok").hexdigest()
            (run / "artifacts.json").write_text(json.dumps({"artifacts": [{"path": "result.txt", "sha256": sha}]}), encoding="utf-8")
            self.assertEqual(verify_run_contract(run)["status"], "PASS")
            self.assertEqual(verify_artifacts(run)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
