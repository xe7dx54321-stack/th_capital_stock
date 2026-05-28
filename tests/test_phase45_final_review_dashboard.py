import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase45_helpers import make_phase45_conn
from build_phase45_final_review_dashboard import build_payload


class Phase45FinalReviewDashboardTests(unittest.TestCase):
    def test_dashboard_points_to_phase46_without_pending(self):
        summary = build_payload(make_phase45_conn())["summary"]
        self.assertEqual(summary["next_phase"], "phase46_paper_watchlist_tracking")
        self.assertEqual(summary["paper_watchlist_readiness"], "paper_watchlist_candidate")
        self.assertEqual(summary["pending_created"], 0)
        self.assertEqual(summary["paper_order_created"], 0)
        self.assertEqual(summary["promotion_allowed_true"], 0)


if __name__ == "__main__":
    unittest.main()
