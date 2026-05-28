import unittest
from phase48_helpers import make_phase48_active_conn
from build_phase48_event_trigger_audit import build_payload

class Phase48EventTriggerAuditTests(unittest.TestCase):
    def test_audit_records(self):
        conn = make_phase48_active_conn()
        p = build_payload(conn, "300308.SZ")
        self.assertGreaterEqual(p["audit_records"], 1)
    def test_audit_no_pending_order_trade(self):
        conn = make_phase48_active_conn()
        p = build_payload(conn, "300308.SZ")
        for r in p["audit_rows"]:
            self.assertFalse(r["pending_created"])
            self.assertFalse(r["paper_order_created"])
            self.assertFalse(r["real_trade_created"])
    def test_audit_has_before_after(self):
        conn = make_phase48_active_conn()
        p = build_payload(conn, "300308.SZ")
        for r in p["audit_rows"]:
            self.assertIn("before_watchlist_status", r)
            self.assertIn("after_watchlist_status", r)
if __name__ == "__main__": unittest.main()
