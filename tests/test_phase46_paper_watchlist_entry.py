import unittest

from phase46_helpers import make_phase46_conn
from build_phase46_paper_watchlist_entry import build_payload


class Phase46PaperWatchlistEntryTests(unittest.TestCase):
    def test_300308_can_be_paper_watchlist_candidate_without_pending(self):
        payload = build_payload(make_phase46_conn(), "300308.SZ")
        entry = payload["paper_watchlist_entry"]
        self.assertEqual(entry["ticker"], "300308.SZ")
        self.assertEqual(entry["watchlist_status"], "paper_watchlist_candidate")
        self.assertTrue(entry["paper_watchlist_allowed"])
        self.assertFalse(entry["pending_human_review_allowed"])
        self.assertFalse(entry["paper_order_allowed"])
        self.assertFalse(entry["real_trade_allowed"])


if __name__ == "__main__":
    unittest.main()
