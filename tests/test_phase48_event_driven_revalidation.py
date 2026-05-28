import unittest
from phase48_helpers import make_phase48_conn
from validate_phase48_event_driven_revalidation import build_payload

class Phase48EventDrivenRevalidationTests(unittest.TestCase):
    def test_revalidation_passes(self):
        conn = make_phase48_conn()
        p = build_payload(conn, "300308.SZ")
        rev = p["event_driven_revalidation"]
        self.assertEqual(rev["overall_status"], "pass")
    def test_sensitive_not_confirmed(self):
        conn = make_phase48_conn()
        p = build_payload(conn, "300308.SZ")
        rev = p["event_driven_revalidation"]
        self.assertFalse(rev["official_consensus_confirmed"])
        self.assertFalse(rev["supplier_share_confirmed"])
        self.assertFalse(rev["customer_allocation_confirmed"])
    def test_no_pending_order_trade(self):
        conn = make_phase48_conn()
        p = build_payload(conn, "300308.SZ")
        rev = p["event_driven_revalidation"]
        self.assertEqual(rev["pending_created"], 0)
        self.assertEqual(rev["paper_order_created"], 0)
        self.assertEqual(rev["real_trade_created"], 0)
if __name__ == "__main__": unittest.main()
