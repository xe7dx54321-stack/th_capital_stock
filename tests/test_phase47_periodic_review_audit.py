import unittest

from phase47_helpers import make_phase47_active_conn
from build_phase47_periodic_review_audit_report import build_payload


class Phase47PeriodicReviewAuditTests(unittest.TestCase):
    def test_audit_records_after_execute(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn, "300308.SZ")
        self.assertGreaterEqual(payload["audit_records"], 1)

    def test_audit_before_after_status(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn, "300308.SZ")
        for row in payload["audit_rows"]:
            self.assertIn("before_status", row)
            self.assertIn("after_status", row)
            self.assertIn("thesis_delta", row)

    def test_audit_no_pending_order_trade(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn, "300308.SZ")
        for row in payload["audit_rows"]:
            self.assertFalse(row["pending_created"])
            self.assertFalse(row["paper_order_created"])
            self.assertFalse(row["real_trade_created"])

    def test_audit_safety(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn, "300308.SZ")
        safety = payload["safety"]
        self.assertTrue(safety["pending_in_audit"])
        self.assertTrue(safety["order_in_audit"])
        self.assertTrue(safety["trade_in_audit"])

    def test_markdown_output(self):
        from build_phase47_periodic_review_audit_report import render_markdown
        conn = make_phase47_active_conn()
        payload = build_payload(conn, "300308.SZ")
        md = render_markdown(payload)
        self.assertIn("Periodic Review Audit", md)


if __name__ == "__main__":
    unittest.main()
