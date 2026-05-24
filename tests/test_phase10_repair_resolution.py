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

from run_phase10_repair_resolution import resolve_tasks
from smr_blocker_repair_queue import get_repair_task, upsert_repair_task


class Phase10RepairResolutionTests(unittest.TestCase):
    def make_task(self, conn, code="VALUATION_NOT_PROMOTION_ELIGIBLE"):
        return upsert_repair_task(
            conn,
            ticker="09988.HK",
            market="H",
            watchlist_id="ai_core",
            blocker_code=code,
            blocker_type="valuation",
            priority="high",
            severity="high",
            fixability="medium",
            expected_impact="may_restore_valuation_gate",
            suggested_fix="repair valuation",
            source_run_ids=["run-1"],
        )

    def test_umbrella_split_is_in_progress_not_resolved(self):
        conn = sqlite3.connect(":memory:")
        task = self.make_task(conn)

        resolve_tasks(conn, ticker="09988.HK", validation_blockers=["PRICE_STALE", "FORWARD_EPS_MISSING"], dry_run=False)
        current = get_repair_task(conn, task["repair_id"])

        self.assertEqual(current["status"], "in_progress")

    def test_blocker_removed_without_replacement_resolves(self):
        conn = sqlite3.connect(":memory:")
        task = self.make_task(conn, code="PRICE_STALE")

        resolve_tasks(conn, ticker="09988.HK", validation_blockers=[], dry_run=False)
        current = get_repair_task(conn, task["repair_id"])

        self.assertEqual(current["status"], "resolved")

    def test_missing_validation_does_not_claim_resolved(self):
        conn = sqlite3.connect(":memory:")
        self.make_task(conn, code="PRICE_STALE")

        payload = resolve_tasks(conn, ticker="09988.HK", validation_blockers=None, dry_run=True)
        result = payload["results"][0]

        self.assertFalse(result["resolution_check"]["validation_provided"])
        self.assertFalse(result["resolution_check"]["is_resolved"])
        self.assertEqual(result["resolution_check"]["reason"], "needs_validation_before_resolution")


if __name__ == "__main__":
    unittest.main()
