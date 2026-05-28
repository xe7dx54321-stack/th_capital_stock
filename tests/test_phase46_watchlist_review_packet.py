import unittest

from phase46_helpers import make_phase46_active_conn
from build_phase46_paper_watchlist_review_packet import build_payload


class Phase46WatchlistReviewPacketTests(unittest.TestCase):
    def test_review_packet_explains_tracking_not_pending(self):
        packet = build_payload(make_phase46_active_conn(), "300308.SZ")["paper_watchlist_review_packet"]
        self.assertEqual(packet["watchlist_status"], "active_tracking")
        self.assertGreaterEqual(len(packet["tracking_variables"]), 10)
        self.assertGreaterEqual(len(packet["tracking_triggers"]), 3)
        self.assertIn("create_pending", packet["forbidden_actions"])
        self.assertIn("create_paper_order", packet["forbidden_actions"])
        self.assertTrue(packet["why_tracking_not_pending"])


if __name__ == "__main__":
    unittest.main()
