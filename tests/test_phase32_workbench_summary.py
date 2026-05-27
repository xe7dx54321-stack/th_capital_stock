import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, REPORTING_DIR, JOBS_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase32_workbench_summary import build_payload, render_markdown
from phase31_helpers import make_conn_with_candidate, phase31_candidate


class Phase32WorkbenchSummaryTests(unittest.TestCase):
    def test_workbench_summary_json_markdown(self):
        conn = make_conn_with_candidate(phase31_candidate(variable_type="customer_allocation_signal", quality_bucket="weak_but_usable", quality_score=58))
        payload = build_payload(conn, tickers="300394.SZ")
        self.assertIn("summary", payload)
        self.assertEqual(payload["summary"]["promotion_allowed_true"], 0)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["summary"]["paper_order_created"], 0)
        self.assertIn("Recommended Review Order", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
