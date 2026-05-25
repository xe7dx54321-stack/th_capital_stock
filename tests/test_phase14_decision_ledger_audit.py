import json
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_decision import ensure_decision_tables, upsert_decision_ledger


class Phase14DecisionLedgerAuditTests(unittest.TestCase):
    def test_ledger_normalizes_reduced_size_audit_fields(self):
        conn = sqlite3.connect(":memory:")
        ensure_decision_tables(conn)
        upsert_decision_ledger(
            conn,
            "phase14-rec",
            "pending_human_review",
            dashboard_summary={"action": "small_candidate 09988.HK", "ticker": "09988.HK", "suggested_position_pct": 0.75},
            metadata={
                "ticker": "09988.HK",
                "promotion_mode": "reduced_size_pending",
                "position_policy": "reduced_size",
                "promotion_evidence_gate": {
                    "thesis_types": ["valuation_rerating"],
                    "core_blockers": [],
                    "optional_warnings": [{"field": "capex"}, {"field": "free_cash_flow"}],
                },
                "thesis_inference": {"primary_thesis_type": "valuation_rerating", "confidence": 0.72},
            },
        )

        row = conn.execute("SELECT metadata_json FROM decision_ledger WHERE recommendation_id='phase14-rec'").fetchone()
        metadata = json.loads(row[0])
        self.assertEqual(metadata["primary_thesis_type"], "valuation_rerating")
        self.assertEqual(metadata["promotion_mode"], "reduced_size_pending")
        self.assertEqual(metadata["optional_warnings"], ["capex", "free_cash_flow"])
        self.assertTrue(metadata["requires_human_review"])
        self.assertFalse(metadata["auto_approval_allowed"])
        self.assertFalse(metadata["paper_order_allowed"])


if __name__ == "__main__":
    unittest.main()
