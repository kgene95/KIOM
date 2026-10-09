import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.preflight_windows import check_runtime


class PreflightTests(unittest.TestCase):
    def test_preflight_checks_a_free_port_and_writable_folder(self):
        with tempfile.TemporaryDirectory() as td:
            errors = check_runtime(Path(td), port=0)
        self.assertFalse([e for e in errors if "writable" in e.lower()])


if __name__ == "__main__":
    unittest.main()
