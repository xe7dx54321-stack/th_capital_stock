import unittest
from phase48_helpers import make_phase48_conn
from run_phase48_event_evidence_refresh import build_payload

class Phase48EventEvidenceRefreshExecutorTests(unittest.TestCase):
    def test_dry_run_no_audit(self):
        conn = make_phase48_conn()
        p = build_payload(conn, "300308.SZ", mode="dry-run")
        ex = p["event_evidence_refresh"]
        self.assertEqual(ex["mode"], "dry-run")
        self.assertFalse(ex["audit_written"])
    def test_execute_writes_audit(self):
        conn = make_phase48_conn()
        p = build_payload(conn, "300308.SZ", mode="execute")
        ex = p["event_evidence_refresh"]
        self.assertTrue(ex["audit_written"])
    def test_no_pending_order_trade(self):
        conn = make_phase48_conn()
        p = build_payload(conn, "300308.SZ", mode="execute")
        ex = p["event_evidence_refresh"]
        self.assertEqual(ex["pending_created"], 0)
        self.assertEqual(ex["paper_order_created"], 0)
        self.assertEqual(ex["real_trade_created"], 0)
    def test_safety(self):
        conn = make_phase48_conn()
        p = build_payload(conn, "300308.SZ", mode="execute")
        s = p["safety"]
        self.assertFalse(s["executor_creates_pending"])
        self.assertFalse(s["promotion_rules_relaxed"])
if __name__ == "__main__": unittest.main()
