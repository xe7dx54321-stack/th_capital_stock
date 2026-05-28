import unittest

from phase46_helpers import make_phase46_conn
from upsert_phase46_paper_watchlist_entry import build_payload


class Phase46WatchlistUpsertTests(unittest.TestCase):
    def test_upsert_is_idempotent_and_does_not_create_order(self):
        conn = make_phase46_conn()
        first = build_payload(conn, ticker="300308.SZ", mode="execute")["watchlist_upsert_result"]
        second = build_payload(conn, ticker="300308.SZ", mode="execute")["watchlist_upsert_result"]
        self.assertTrue(first["entry_created"])
        self.assertEqual(first["watchlist_status"], "active_tracking")
        self.assertTrue(second["duplicate_skipped"])
        self.assertEqual(second["pending_created"], 0)
        self.assertEqual(second["paper_order_created"], 0)
        self.assertEqual(second["real_trade_created"], 0)


if __name__ == "__main__":
    unittest.main()
