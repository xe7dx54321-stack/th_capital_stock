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

from build_phase30_semantic_evidence_hardening_summary import build_payload, render_markdown


class Phase30SemanticEvidenceHardeningSummaryTests(unittest.TestCase):
    def test_summary_json_and_markdown(self):
        payload = build_payload(sqlite3.connect(":memory:"), tickers="300394.SZ")
        self.assertIn("quality_distribution", payload)
        self.assertIn("noise_distribution", payload)
        md = render_markdown(payload)
        self.assertIn("Phase 30 Semantic Evidence Quality", md)


if __name__ == "__main__":
    unittest.main()
