import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_blocker_repair_queue import apply_phase14_thesis_metadata, upsert_repair_task


class Phase14RepairQueueMetadataTests(unittest.TestCase):
    def test_optional_missing_records_thesis_without_resolving_task(self):
        conn = sqlite3.connect(":memory:")
        task = upsert_repair_task(
            conn,
            ticker="09988.HK",
            market="H",
            watchlist_id="ai_core",
            blocker_code="FIELD_NOT_FOUND",
            blocker_type="fundamentals",
            priority="medium",
            severity="medium",
            fixability="medium",
            expected_impact="improve_field_coverage",
            suggested_fix="extract capex",
            source_run_ids=["run-1"],
            affected_fields=["capex"],
        )
        update = apply_phase14_thesis_metadata(
            conn,
            ticker="09988.HK",
            thesis_type="valuation_rerating",
            field_gate={
                "gate_status": "pass_with_warnings",
                "optional_warnings": [{"field": "capex"}],
                "supporting_warnings": [],
                "core_blockers": [],
            },
            data_quality_gate={"status": "degraded_non_core"},
        )
        updated = update["phase14_updated_tasks"][0]

        self.assertEqual(task["repair_id"], updated["repair_id"])
        self.assertNotEqual(updated["status"], "resolved")
        self.assertEqual(updated["metadata"]["thesis_type"], "valuation_rerating")
        self.assertEqual(updated["metadata"]["classification"], "optional_missing")
        self.assertTrue(updated["metadata"]["non_blocking_warning"])
        self.assertTrue(updated["metadata"]["still_should_repair"])

    def test_core_missing_remains_open_for_cash_flow_thesis(self):
        conn = sqlite3.connect(":memory:")
        upsert_repair_task(
            conn,
            ticker="09988.HK",
            market="H",
            watchlist_id="ai_core",
            blocker_code="FIELD_NOT_FOUND",
            blocker_type="fundamentals",
            priority="high",
            severity="high",
            fixability="medium",
            expected_impact="blocks_cash_flow_thesis",
            suggested_fix="extract free cash flow",
            source_run_ids=["run-1"],
            affected_fields=["free_cash_flow"],
        )
        update = apply_phase14_thesis_metadata(
            conn,
            ticker="09988.HK",
            thesis_type="cash_flow_improvement",
            field_gate={
                "gate_status": "blocked",
                "optional_warnings": [],
                "supporting_warnings": [],
                "core_blockers": [{"field": "free_cash_flow"}],
            },
            data_quality_gate={"status": "degraded_core"},
        )
        updated = update["phase14_updated_tasks"][0]

        self.assertEqual(updated["status"], "open")
        self.assertFalse(updated["metadata"]["non_blocking_warning"])
        self.assertEqual(updated["metadata"]["classification"], "core_missing")


if __name__ == "__main__":
    unittest.main()
