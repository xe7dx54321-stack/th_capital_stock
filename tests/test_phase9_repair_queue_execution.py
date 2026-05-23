import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(JOBS_DIR) not in sys.path:
    sys.path.insert(0, str(JOBS_DIR))

from run_phase9_repair_queue import execute_task, select_tasks
from smr_blocker_repair_queue import get_repair_task, upsert_repair_task


class Phase9RepairQueueExecutionTests(unittest.TestCase):
    def make_task(self, conn):
        return upsert_repair_task(
            conn,
            ticker="09988.HK",
            market="HK",
            watchlist_id="ai_core",
            blocker_code="VALUATION_NOT_PROMOTION_ELIGIBLE",
            blocker_type="valuation",
            priority="high",
            severity="high",
            fixability="medium",
            expected_impact="may_restore_valuation_gate",
            suggested_fix="repair valuation",
            source_run_ids=["run-1"],
        )

    def test_dry_run_does_not_change_status(self):
        conn = sqlite3.connect(":memory:")
        task = self.make_task(conn)
        result = execute_task(conn, task, dry_run=True)
        current = get_repair_task(conn, task["repair_id"])

        self.assertEqual(result["mode"], "dry_run")
        self.assertEqual(current["status"], "open")

    def test_execute_updates_status_and_metadata(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE daily_bar (ts_code TEXT, market TEXT, trade_date TEXT, close REAL)")
        conn.execute("INSERT INTO daily_bar VALUES ('09988.HK', 'H', '2026-05-22', 80.0)")
        task = self.make_task(conn)
        result = execute_task(conn, task, dry_run=False)
        current = get_repair_task(conn, task["repair_id"])

        self.assertEqual(result["mode"], "execute")
        self.assertIn(current["status"], {"needs_manual_review", "resolved", "open"})
        self.assertIn("phase9_execution_result", current["metadata"])


if __name__ == "__main__":
    unittest.main()
