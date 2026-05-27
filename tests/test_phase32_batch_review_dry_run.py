import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, JOBS_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase31_helpers import make_conn_with_candidate, phase31_candidate
from run_phase32_batch_review_dry_run import build_payload


class Phase32BatchReviewDryRunTests(unittest.TestCase):
    def test_batch_dry_run_does_not_write_or_allow_promotion(self):
        conn = make_conn_with_candidate(phase31_candidate(variable_type="customer_allocation_signal", quality_bucket="weak_but_usable", quality_score=58))
        payload = build_payload(conn, priority="high")
        summary = payload["summary"]
        self.assertGreaterEqual(summary["items_checked"], 1)
        self.assertEqual(summary["promotion_allowed_after_actions"], 0)
        self.assertEqual(summary["new_pending_created"], 0)
        self.assertEqual(summary["paper_order_created"], 0)
        self.assertFalse(payload["safety"]["dry_run_wrote_db"])


if __name__ == "__main__":
    unittest.main()
