import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase45_helpers import make_phase45_conn
from build_phase45_paper_watchlist_readiness_packet import build_payload


class Phase45PaperWatchlistReadinessTests(unittest.TestCase):
    def test_paper_watchlist_candidate_is_tracking_only(self):
        body = build_payload(make_phase45_conn(), "300308.SZ")["paper_watchlist_readiness_packet"]
        boundary = body["entry_boundary"]
        self.assertEqual(body["readiness"], "paper_watchlist_candidate")
        self.assertTrue(boundary["paper_watchlist_allowed"])
        self.assertFalse(boundary["paper_order_allowed"])
        self.assertFalse(boundary["pending_human_review_allowed"])
        self.assertFalse(boundary["real_trade_allowed"])


if __name__ == "__main__":
    unittest.main()
