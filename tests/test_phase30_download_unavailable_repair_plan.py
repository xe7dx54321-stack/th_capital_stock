import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase30_download_unavailable_repair_plan import build_payload


class Phase30DownloadUnavailableRepairPlanTests(unittest.TestCase):
    def test_repair_plan_outputs_actions_without_writing_evidence(self):
        payload = build_payload(sqlite3.connect(":memory:"), tickers="300394.SZ")
        self.assertIn("summary", payload)
        self.assertFalse(payload["safety"]["ocr_default_enabled"])
        self.assertFalse(payload["safety"]["evidence_written"])


if __name__ == "__main__":
    unittest.main()
