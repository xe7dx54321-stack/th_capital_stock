import unittest

from phase46_helpers import make_phase46_active_conn
from update_phase46_watchlist_status import build_payload as update_status
from validate_phase46_watchlist_status_update import build_payload as validate_update


class Phase46WatchlistStatusUpdateTests(unittest.TestCase):
    def test_status_update_does_not_create_order(self):
        conn = make_phase46_active_conn()
        update = update_status(conn, ticker="300308.SZ", status="tracking_strengthened", mode="execute")["watchlist_status_update"]
        self.assertEqual(update["before_status"], "active_tracking")
        self.assertEqual(update["after_status"], "tracking_strengthened")
        self.assertTrue(update["audit_written"])
        self.assertEqual(update["pending_created"], 0)
        self.assertEqual(update["paper_order_created"], 0)
        self.assertEqual(update["real_trade_created"], 0)
        validation = validate_update(conn, "300308.SZ")
        self.assertEqual(validation["overall_status"], "pass")

    def test_forbidden_status_update_is_blocked(self):
        conn = make_phase46_active_conn()
        update = update_status(conn, ticker="300308.SZ", status="paper_order", mode="dry_run")["watchlist_status_update"]
        self.assertFalse(update["transition_allowed"])


if __name__ == "__main__":
    unittest.main()
