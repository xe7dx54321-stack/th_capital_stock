import unittest

from phase47_helpers import make_phase47_active_conn
from build_phase47_periodic_review_dashboard import build_payload


class Phase47PeriodicReviewDashboardTests(unittest.TestCase):
    def test_dashboard_reviews_completed(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn)
        summary = payload["summary"]
        self.assertGreaterEqual(summary["watchlist_entries"], 1)
        self.assertGreaterEqual(summary["reviews_completed"], 1)

    def test_dashboard_no_pending_order_trade(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn)
        summary = payload["summary"]
        self.assertEqual(summary["pending_created"], 0)
        self.assertEqual(summary["paper_order_created"], 0)
        self.assertEqual(summary["real_trade_created"], 0)

    def test_dashboard_ticker_rows(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn)
        rows = payload["ticker_rows"]
        self.assertGreaterEqual(len(rows), 1)
        row = rows[0]
        self.assertIn("ticker", row)
        self.assertIn("watchlist_status", row)
        self.assertIn("review_status", row)
        self.assertIn("thesis_strength_score", row)
        self.assertFalse(row["pending_allowed"])
        self.assertFalse(row["paper_order_allowed"])

    def test_dashboard_safety(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn)
        safety = payload["safety"]
        self.assertFalse(safety["dashboard_creates_pending"])
        self.assertFalse(safety["dashboard_creates_order"])
        self.assertFalse(safety["dashboard_creates_trade"])
        self.assertFalse(safety["promotion_rules_relaxed"])
        self.assertFalse(safety["real_trade_risk"])

    def test_markdown_output(self):
        from build_phase47_periodic_review_dashboard import render_markdown
        conn = make_phase47_active_conn()
        payload = build_payload(conn)
        md = render_markdown(payload)
        self.assertIn("Periodic Review Dashboard", md)
        self.assertIn("Summary", md)


if __name__ == "__main__":
    unittest.main()
