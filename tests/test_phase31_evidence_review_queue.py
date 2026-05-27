import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase31_helpers import make_conn_with_candidate, phase31_candidate
from smr_evidence_review_queue import build_review_queue


class Phase31EvidenceReviewQueueTests(unittest.TestCase):
    def test_sensitive_variable_enters_queue(self):
        conn = make_conn_with_candidate(phase31_candidate(variable_type="customer_allocation_signal", quality_bucket="weak_but_usable", quality_score=58))
        payload = build_review_queue(conn, ticker="300394.SZ")
        self.assertGreaterEqual(payload["summary"]["review_queue_items"], 1)
        self.assertGreaterEqual(payload["summary"]["sensitive_variable_items"], 1)

    def test_plain_usable_candidate_can_stay_out_of_queue(self):
        conn = make_conn_with_candidate()
        payload = build_review_queue(conn, ticker="300394.SZ")
        self.assertEqual(payload["summary"]["promotion_allowed_true"], 0)


if __name__ == "__main__":
    unittest.main()
