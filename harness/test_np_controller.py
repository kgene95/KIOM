import json
import tempfile
import unittest
from pathlib import Path

from np_controller import ControllerBusy, controller_lease, dispatch_ready_tasks, recover_orphans
from np_harness import transition_task


class ControllerTests(unittest.TestCase):
    def test_state_transition_guard_rejects_terminal_jump(self):
        task = {"id": "x", "status": "QUEUED"}
        with self.assertRaises(ValueError):
            transition_task(task, "RUNNING")
        transition_task(task, "READY_FOR_WORKER")
        transition_task(task, "RUNNING")
        transition_task(task, "DONE")
        self.assertEqual(task["status"], "DONE")

    def test_run_lease_blocks_second_controller(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            with controller_lease(run):
                with self.assertRaises(ControllerBusy):
                    with controller_lease(run):
                        pass

    def test_expired_worker_lease_is_recovered(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            queue = {"tasks": [{"id": "initial_ppi", "status": "RUNNING", "lease_until": "2000-01-01T00:00:00+00:00", "worker_pid": 123}]}
            recovered = recover_orphans(run, queue)
            self.assertEqual(recovered["tasks"][0]["status"], "RETRY_WAIT")
            self.assertIn('"event": "orphan_recovered"', (run / "event_log.jsonl").read_text(encoding="utf-8"))

    def test_done_without_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            queue = {"tasks": [{"id": "initial_ppi", "status": "READY_FOR_WORKER", "requires": [], "attempts": 0}]}
            result = dispatch_ready_tasks(run, queue, {"initial_ppi": lambda path: {"status": "DONE", "outputs": ["missing.csv"]}})
            self.assertEqual(result["tasks"][0]["status"], "FAILED")
            self.assertTrue((run / "controller_alert.json").exists())

    def test_dispatch_runs_ready_worker_and_records_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            queue = {"tasks": [{"id": "initial_ppi", "agent": "agent3", "requires": [], "status": "READY_FOR_WORKER", "attempts": 0}]}
            called = []

            def worker(path):
                called.append(path)
                (path / "ppi.csv").write_text("node\n", encoding="utf-8")
                return {"status": "DONE", "outputs": ["ppi.csv"]}

            result = dispatch_ready_tasks(run, queue, {"initial_ppi": worker})
            self.assertEqual(called, [run])
            self.assertEqual(result["tasks"][0]["status"], "DONE")
            events = (run / "event_log.jsonl").read_text(encoding="utf-8")
            self.assertIn('"event": "worker_started"', events)
            self.assertIn('"event": "worker_completed"', events)

    def test_dispatch_captures_worker_failure_and_bounds_retries(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            queue = {"tasks": [{"id": "initial_ppi", "agent": "agent3", "requires": [], "status": "READY_FOR_WORKER", "attempts": 2}]}

            def worker(path):
                raise RuntimeError("network unavailable")

            result = dispatch_ready_tasks(run, queue, {"initial_ppi": worker}, max_attempts=3)
            task = result["tasks"][0]
            self.assertEqual(task["status"], "FAILED")
            self.assertIn("network unavailable", task["detail"])
            self.assertIn('"event": "worker_failed"', (run / "event_log.jsonl").read_text(encoding="utf-8"))
            self.assertTrue((run / "controller_alert.json").exists())

    def test_dispatch_retries_retry_wait_on_next_cycle(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            queue = {"tasks": [{"id": "initial_ppi", "agent": "agent3", "requires": [], "status": "READY_FOR_WORKER", "attempts": 0}]}

            def worker(path):
                raise RuntimeError("temporary failure")

            queue = dispatch_ready_tasks(run, queue, {"initial_ppi": worker}, max_attempts=2)
            self.assertEqual(queue["tasks"][0]["status"], "RETRY_WAIT")
            queue["tasks"][0]["next_attempt_at"] = "2000-01-01T00:00:00+00:00"
            queue = dispatch_ready_tasks(run, queue, {"initial_ppi": worker}, max_attempts=2)
            self.assertEqual(queue["tasks"][0]["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
