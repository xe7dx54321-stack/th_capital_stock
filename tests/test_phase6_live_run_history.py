import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_live_run_history import (
    compare_live_run_history,
    ensure_live_run_history_tables,
    latest_live_run_history,
    record_live_run_history,
)


class Phase6LiveRunHistoryTests(unittest.TestCase):
    def make_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        ensure_live_run_history_tables(conn)
        return conn

    def test_history_records_and_compares_ticker_status(self):
        conn = self.make_conn()
        previous = record_live_run_history(
            conn,
            run_id="run-prev",
            watchlist_id="ai_core",
            ticker_rows=[
                {"ticker": "NVDA", "status": "observation_only", "action": "observation", "summary_bucket": "observation_only", "promotion_debugger": {"blocking_factors": [{"code": "A", "detail": "a"}]}},
                {"ticker": "AVGO", "status": "candidate_shadow", "action": "watch", "summary_bucket": "candidate_shadow"},
            ],
        )
        current = record_live_run_history(
            conn,
            run_id="run-now",
            watchlist_id="ai_core",
            ticker_rows=[
                {"ticker": "NVDA", "status": "pending_human_review", "action": "small_candidate", "summary_bucket": "pending_human_review", "promotion_debugger": {"blocking_factors": []}},
                {"ticker": "AVGO", "status": "candidate_shadow", "action": "watch", "summary_bucket": "candidate_shadow", "promotion_debugger": {"blocking_factors": [{"code": "B", "detail": "b"}]}},
            ],
        )

        latest = latest_live_run_history(conn, "ai_core")
        comparison = compare_live_run_history(previous, current)

        self.assertEqual(latest["run_id"], "run-now")
        self.assertIn("NVDA", comparison["improved"])
        self.assertIn("AVGO", comparison["repeated_blockers"])
        self.assertEqual(current["pending_count"], 1)
        self.assertEqual(current["candidate_shadow_count"], 1)


if __name__ == "__main__":
    unittest.main()
