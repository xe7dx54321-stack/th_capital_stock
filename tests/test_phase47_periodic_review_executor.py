import unittest

from phase47_helpers import make_phase47_conn
from run_phase47_periodic_watchlist_review import build_payload


class Phase47PeriodicReviewExecutorTests(unittest.TestCase):
    def test_dry_run_no_audit_written(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ", mode="dry-run")
        exec_data = payload["periodic_review_execution"]
        self.assertEqual(exec_data["mode"], "dry-run")
        self.assertFalse(exec_data["audit_written"])
        self.assertEqual(exec_data["pending_created"], 0)
        self.assertEqual(exec_data["paper_order_created"], 0)
        self.assertEqual(exec_data["real_trade_created"], 0)

    def test_execute_writes_audit(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ", mode="execute")
        exec_data = payload["periodic_review_execution"]
        self.assertEqual(exec_data["mode"], "execute")
        self.assertTrue(exec_data["audit_written"])

    def test_execute_no_pending_order_trade(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ", mode="execute")
        exec_data = payload["periodic_review_execution"]
        self.assertEqual(exec_data["pending_created"], 0)
        self.assertEqual(exec_data["paper_order_created"], 0)
        self.assertEqual(exec_data["real_trade_created"], 0)

    def test_execute_safety_gates(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ", mode="execute")
        safety = payload["safety"]
        self.assertFalse(safety["executor_creates_pending"])
        self.assertFalse(safety["executor_creates_order"])
        self.assertFalse(safety["executor_creates_trade"])
        self.assertFalse(safety["promotion_rules_relaxed"])
        self.assertFalse(safety["real_trade_risk"])

    def test_execute_thesis_delta_unchanged(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ", mode="execute")
        exec_data = payload["periodic_review_execution"]
        self.assertEqual(exec_data["thesis_delta"], "unchanged")


if __name__ == "__main__":
    unittest.main()
