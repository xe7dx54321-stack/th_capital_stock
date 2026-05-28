import unittest
from phase48_helpers import make_phase48_active_conn
from build_phase48_event_watchlist_dashboard import build_payload

class Phase48EventWatchlistDashboardTests(unittest.TestCase):
    def test_dashboard_has_summary(self):
        conn = make_phase48_active_conn()
        p = build_payload(conn)
        s = p["summary"]
        self.assertGreaterEqual(s["watchlist_entries"], 1)
        self.assertGreaterEqual(s["event_refresh_completed"], 1)
    def test_no_pending_order_trade(self):
        conn = make_phase48_active_conn()
        p = build_payload(conn)
        s = p["summary"]
        self.assertEqual(s["pending_created"], 0)
        self.assertEqual(s["paper_order_created"], 0)
        self.assertEqual(s["real_trade_created"], 0)
    def test_ticker_rows(self):
        conn = make_phase48_active_conn()
        p = build_payload(conn)
        self.assertGreaterEqual(len(p["ticker_rows"]), 1)
        r = p["ticker_rows"][0]
        self.assertFalse(r["pending_allowed"])
        self.assertFalse(r["paper_order_allowed"])
    def test_markdown(self):
        from build_phase48_event_watchlist_dashboard import render_markdown
        conn = make_phase48_active_conn()
        md = render_markdown(build_payload(conn))
        self.assertIn("Event Watchlist Dashboard", md)
if __name__ == "__main__": unittest.main()
