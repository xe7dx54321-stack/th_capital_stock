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

from smr_blocker_repair_queue import list_repair_tasks, upsert_phase21_evidence_repair_task
from upsert_bear_case_evidence_repair_tasks import dry_run_task, task_type_for_missing


class Phase21BearCaseRepairTasksTests(unittest.TestCase):
    def test_missing_evidence_maps_to_repair_task_type(self):
        self.assertEqual(task_type_for_missing("direct AI order/customer demand evidence"), "ORDER_EVIDENCE_MISSING")
        self.assertEqual(task_type_for_missing("second independent demand evidence source"), "PROXY_INDEPENDENT_SOURCE_MISSING")

    def test_repair_task_upsert_deduplicates(self):
        conn = sqlite3.connect(":memory:")
        kwargs = {
            "ticker": "TEST.SZ",
            "watchlist_id": "ai_core",
            "task_type": "DIRECT_DEMAND_EVIDENCE_MISSING",
            "priority": "high",
            "source_bear_case_claim_id": "bear_1",
            "missing_evidence": "direct demand evidence",
            "suggested_sources": ["annual report"],
            "gate_type": "BEAR_CASE_GATE",
        }
        first = upsert_phase21_evidence_repair_task(conn, **kwargs)
        second = upsert_phase21_evidence_repair_task(conn, **kwargs)

        self.assertEqual(first["repair_id"], second["repair_id"])
        self.assertEqual(len(list_repair_tasks(conn, ticker="TEST.SZ", watchlist_id="ai_core")), 1)

    def test_dry_run_task_keeps_source_bear_case_claim_id(self):
        task = dry_run_task(
            "TEST.SZ",
            "ai_core",
            {"bear_case_claim_id": "bear_core", "core_to_thesis": True, "residual_risk_level": "high"},
            "direct demand evidence",
        )

        self.assertEqual(task["source_bear_case_claim_id"], "bear_core")
        self.assertEqual(task["priority"], "high")


if __name__ == "__main__":
    unittest.main()
