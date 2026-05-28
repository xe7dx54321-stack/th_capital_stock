import unittest

from phase46_helpers import make_phase46_active_conn
from build_phase46_watchlist_audit_report import build_payload


class Phase46WatchlistAuditTests(unittest.TestCase):
    def test_audit_has_before_after_without_pending_or_order(self):
        audit = build_payload(make_phase46_active_conn(), "300308.SZ")["watchlist_audit_report"]
        self.assertGreaterEqual(audit["audit_records"], 1)
        record = audit["records"][0]
        self.assertTrue(record["before_status"])
        self.assertTrue(record["after_status"])
        self.assertEqual(audit["pending_created"], 0)
        self.assertEqual(audit["paper_order_created"], 0)
        self.assertEqual(audit["real_trade_created"], 0)


if __name__ == "__main__":
    unittest.main()
