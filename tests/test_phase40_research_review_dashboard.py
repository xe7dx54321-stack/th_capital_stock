import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase40_research_review_dashboard import build_payload
from phase39_helpers import make_phase39_conn
from phase40_helpers import make_phase40_conn_with_action


class Phase40ResearchReviewDashboardTests(unittest.TestCase):
    def test_dashboard_reports_queue_and_repair_without_pending(self):
        payload = build_payload(make_phase39_conn())
        summary = payload["summary"]
        self.assertEqual(summary["research_review_queue_items"], 1)
        self.assertEqual(summary["repair_required_before_review"], 1)
        self.assertEqual(summary["pending_created"], 0)
        self.assertEqual(summary["paper_order_created"], 0)
        self.assertEqual(summary["promotion_allowed_true"], 0)

    def test_dashboard_counts_executed_review_action(self):
        payload = build_payload(make_phase40_conn_with_action())
        self.assertEqual(payload["summary"]["reviewed_request_deeper_research"], 1)
        self.assertFalse(payload["safety"]["real_trade_risk"])


if __name__ == "__main__":
    unittest.main()
