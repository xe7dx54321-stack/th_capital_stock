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
from smr_evidence_review_workbench import build_workbench, filter_workbench_items


class Phase32EvidenceReviewWorkbenchTests(unittest.TestCase):
    def test_workbench_item_generation_and_preview(self):
        conn = make_conn_with_candidate(phase31_candidate(variable_type="customer_allocation_signal", quality_bucket="weak_but_usable", quality_score=58))
        payload = build_workbench(conn, ticker="300394.SZ", include_generated=False)
        self.assertGreaterEqual(payload["summary"]["total_workbench_items"], 1)
        item = payload["items"][0]
        self.assertTrue(item["sensitive_variable"])
        self.assertIn("upgrade_to_confirmed_customer_allocation", item["blocked_actions"])
        self.assertLessEqual(len(item["quoted_span_preview"]), 220)
        self.assertEqual(payload["summary"]["promotion_allowed_true"], 0)

    def test_high_priority_and_sensitive_filters(self):
        conn = make_conn_with_candidate(phase31_candidate(variable_type="customer_allocation_signal", quality_bucket="weak_but_usable", quality_score=58))
        items = build_workbench(conn, ticker="300394.SZ", include_generated=False)["items"]
        self.assertTrue(filter_workbench_items(items, priority="high"))
        self.assertTrue(filter_workbench_items(items, sensitive_only=True))


if __name__ == "__main__":
    unittest.main()
