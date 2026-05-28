import unittest

from phase46_helpers import make_phase46_active_conn
from build_phase46_paper_watchlist_dashboard import build_payload
from update_phase46_watchlist_status import build_payload as update_status


class Phase46WatchlistDashboardTests(unittest.TestCase):
    def test_dashboard_reports_tracking_pool_without_pending_order_trade(self):
        conn = make_phase46_active_conn()
        update_status(conn, ticker="300308.SZ", status="tracking_strengthened", mode="execute")
        dashboard = build_payload(conn)
        summary = dashboard["summary"]
        self.assertEqual(summary["watchlist_entries"], 1)
        self.assertEqual(summary["active_tracking"], 1)
        self.assertEqual(summary["tracking_strengthened"], 1)
        self.assertEqual(summary["pending_created"], 0)
        self.assertEqual(summary["paper_orders_created"], 0)
        self.assertEqual(summary["real_trades_created"], 0)
        row = dashboard["ticker_rows"][0]
        self.assertEqual(row["ticker"], "300308.SZ")
        self.assertFalse(row["paper_order_allowed"])
        self.assertFalse(row["pending_allowed"])


if __name__ == "__main__":
    unittest.main()
