import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_blocker_repair_queue import (
    list_repair_tasks,
    repair_id_for,
    update_repair_task_status,
    upsert_repair_task,
)


class BlockerRepairQueueTests(unittest.TestCase):
    def test_upsert_deduplicates_ticker_blocker_and_merges_runs(self):
        conn = sqlite3.connect(":memory:")
        first = upsert_repair_task(
            conn,
            ticker="09988.HK",
            market="HK",
            watchlist_id="ai_core",
            blocker_code="FUNDAMENTALS_MISSING_FIELDS",
            blocker_type="fundamentals",
            priority="high",
            severity="high",
            fixability="medium",
            expected_impact="may_upgrade_candidate_shadow_to_pending_review",
            suggested_fix="improve HKEX parser",
            source_run_ids=["run-1"],
            affected_fields=["gross_profit"],
        )
        second = upsert_repair_task(
            conn,
            ticker="09988.HK",
            market="HK",
            watchlist_id="ai_core",
            blocker_code="FUNDAMENTALS_MISSING_FIELDS",
            blocker_type="fundamentals",
            priority="high",
            severity="high",
            fixability="medium",
            expected_impact="may_upgrade_candidate_shadow_to_pending_review",
            suggested_fix="improve HKEX parser",
            source_run_ids=["run-2"],
            affected_fields=["capex"],
        )
        tasks = list_repair_tasks(conn, status="open")

        self.assertEqual(first["repair_id"], second["repair_id"])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(set(tasks[0]["source_run_ids"]), {"run-1", "run-2"})
        self.assertEqual(set(tasks[0]["affected_fields"]), {"gross_profit", "capex"})

    def test_status_update_records_owner_and_note(self):
        conn = sqlite3.connect(":memory:")
        task = upsert_repair_task(
            conn,
            ticker="00700.HK",
            market="HK",
            watchlist_id="ai_core",
            blocker_code="PROXY_INVALID",
            blocker_type="proxy",
            priority="high",
            severity="high",
            fixability="medium",
            expected_impact="may_upgrade_proxy_to_promotion_grade",
            suggested_fix="extract proxy",
            source_run_ids=["run-1"],
        )

        updated = update_repair_task_status(conn, task["repair_id"], "in_progress", owner="codex", note="working")

        self.assertEqual(updated["status"], "in_progress")
        self.assertEqual(updated["owner"], "codex")
        self.assertIn("status_notes", updated["metadata"])
        self.assertEqual(task["repair_id"], repair_id_for("00700.HK", "PROXY_INVALID", "ai_core"))


if __name__ == "__main__":
    unittest.main()
