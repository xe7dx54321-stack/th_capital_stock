import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, REPORTING_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase26_variable_evidence_summary import build_payload, render_markdown
from test_phase26_capacity_shipment_evidence import make_capacity_conn


class Phase26VariableEvidenceSummaryTests(unittest.TestCase):
    def test_summary_json_and_markdown(self):
        payload = build_payload(make_capacity_conn(), tickers="300394.SZ")
        markdown = render_markdown(payload)
        self.assertEqual(payload["summary"]["tickers_checked"], 1)
        self.assertIn("promotion_allowed_from_variable_evidence", payload["summary"])
        self.assertIn("300394.SZ", markdown)
        self.assertIn("# Phase 26 Supply Chain Variable Evidence Summary", markdown)


if __name__ == "__main__":
    unittest.main()
