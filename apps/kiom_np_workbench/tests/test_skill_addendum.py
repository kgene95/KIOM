import unittest
from pathlib import Path


class SkillAddendumTests(unittest.TestCase):
    def test_np_skill_addendum_contains_source_and_qc_contract(self):
        text = (Path(__file__).resolve().parents[1] / "docs" / "NP_SKILL_ADDENDUM.md").read_text(encoding="utf-8")
        for required in ("provenance_status", "UNVERIFIED", "ZIP", "TSV", "hub_topology_degree.csv", "FDR"):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
