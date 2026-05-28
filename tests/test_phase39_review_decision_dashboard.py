import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase39_review_decision_dashboard import build_payload
from phase39_helpers import make_phase39_conn


class Phase39ReviewDecisionDashboardTests(unittest.TestCase):
    def test_dashboard_reports_review_decision_without_pending_or_order(self):
        payload = build_payload(make_phase39_conn())
        summary = payload["summary"]
        self.assertEqual(summary["300308_decision"], "research_review_candidate")
        self.assertEqual(summary["300394_status"], "repair_required_before_research_deepening")
        self.assertFalse(summary["300308_pending_allowed"])
        self.assertEqual(summary["new_pending_created"], 0)
        self.assertEqual(summary["paper_order_created"], 0)
        self.assertEqual(summary["promotion_allowed_true"], 0)
        self.assertFalse(payload["safety"]["real_trade_risk"])


if __name__ == "__main__":
    unittest.main()
