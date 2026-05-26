import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
for path in (LIB_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_blocker_repair_queue import list_repair_tasks, upsert_phase22_valuation_demand_repair_task
from upsert_phase22_valuation_demand_repair_tasks import dry_run_task, task_type_for_gap


class Phase22RepairTasksTests(unittest.TestCase):
    def test_gap_maps_to_phase22_task_type(self):
        self.assertEqual(task_type_for_gap("FORWARD_EPS_PROXY_ONLY", gate_type="VALUATION_GATE"), "FORWARD_EPS_PROXY_ONLY")
        self.assertEqual(task_type_for_gap("tender or procurement evidence missing", gate_type="DEMAND_EVIDENCE_GATE"), "TENDER_EVIDENCE_MISSING")

    def test_dry_run_task_has_priority_and_suggested_sources(self):
        task = dry_run_task("TEST.SZ", "ai_core", gate_type="DEMAND_EVIDENCE_GATE", missing_evidence="confirmed signed order missing")
        self.assertEqual(task["priority"], "high")
        self.assertTrue(task["suggested_sources"])

    def test_phase22_upsert_deduplicates(self):
        conn = sqlite3.connect(":memory:")
        kwargs = {
            "ticker": "TEST.SZ",
            "watchlist_id": "ai_core",
            "task_type": "FORWARD_EPS_PROXY_ONLY",
            "priority": "medium",
            "gate_type": "VALUATION_GATE",
            "missing_evidence": "FORWARD_EPS_PROXY_ONLY",
            "suggested_sources": ["official consensus source"],
        }
        first = upsert_phase22_valuation_demand_repair_task(conn, **kwargs)
        second = upsert_phase22_valuation_demand_repair_task(conn, **kwargs)
        self.assertEqual(first["repair_id"], second["repair_id"])
        self.assertEqual(len(list_repair_tasks(conn, ticker="TEST.SZ", watchlist_id="ai_core")), 1)


if __name__ == "__main__":
    unittest.main()
