import unittest

from phase46_helpers import make_phase46_conn
from smr_paper_watchlist_lifecycle import build_watchlist_transition, validate_watchlist_transition


class Phase46WatchlistLifecycleTests(unittest.TestCase):
    def test_lifecycle_allows_candidate_to_active_tracking(self):
        transition = build_watchlist_transition(ticker="300308.SZ")
        self.assertTrue(transition["transition_allowed"])
        self.assertEqual(transition["after_status"], "active_tracking")
        self.assertFalse(transition["pending_created"])
        self.assertFalse(transition["paper_order_created"])
        self.assertFalse(transition["real_trade_created"])

    def test_lifecycle_blocks_pending_order_trade_states(self):
        for status in ("pending_human_review", "paper_order", "real_trade"):
            ok, reason = validate_watchlist_transition("active_tracking", status)
            self.assertFalse(ok)
            self.assertIn("forbidden", reason)


if __name__ == "__main__":
    unittest.main()
