import tempfile
import unittest
from pathlib import Path

from simulation import run_simulation


class HarnessSimulationTests(unittest.TestCase):
    def test_wrong_sea_upload_is_quarantined_then_correct_upload_completes_run(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_simulation(Path(temp))

            self.assertEqual(result["status"], "DONE")
            self.assertEqual(result["wrong_upload_status"], "IDENTITY_MISMATCH")
            self.assertEqual(result["correct_upload_status"], "DONE")
            self.assertTrue(result["artifacts"]["analysis_summary"].exists())
            self.assertTrue(result["artifacts"]["figure_draft"].exists())
            self.assertTrue(result["artifacts"]["docking_candidates"].exists())
            self.assertTrue(result["artifacts"]["quarantine"].exists())
            self.assertIn("external_event_rejected", result["events"])
            self.assertIn("external_event_routed", result["events"])
            self.assertIn("simulation_recovered", result["events"])
            self.assertIn("simulation_dispatch_contract_validated", result["events"])


if __name__ == "__main__":
    unittest.main()
