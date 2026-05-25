import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase15_review_ops_summary import build_ops_payload
from smr_decision import upsert_decision_ledger
from smr_registry import register_snapshot


class Phase15ReviewOpsSummaryTests(unittest.TestCase):
    def test_ops_summary_surfaces_review_repair_and_unknown_tasks(self):
        conn = sqlite3.connect(":memory:")
        register_snapshot(
            conn,
            entity_type="phase14_thesis_aware_multi_ticker_live_validation",
            entity_id="ai_core",
            status="partial_pass",
            source="test",
            payload={
                "summary": {"overall_result": "partial_pass"},
                "watchlist_id": "ai_core",
                "tickers": [
                    {
                        "ticker": "09988.HK",
                        "after_status": "pending_human_review",
                        "primary_thesis_type": "valuation_rerating",
                        "promotion_mode": "reduced_size_pending",
                        "optional_warnings": ["capex", "free_cash_flow"],
                    },
                    {
                        "ticker": "00700.HK",
                        "after_status": "candidate_shadow",
                        "primary_thesis_type": "valuation_rerating",
                        "core_blockers": ["shareholders_equity"],
                    },
                    {
                        "ticker": "002230.SZ",
                        "after_status": "candidate_shadow",
                        "primary_thesis_type": "unknown",
                        "thesis_inference_confidence": 0.29,
                        "thesis_inference": {"confidence": 0.29, "signals_used": []},
                    },
                ],
            },
        )
        upsert_decision_ledger(
            conn,
            "phase14_thesis_aware__09988.HK__valuation_rerating",
            "pending_human_review",
            dashboard_summary={"action": "small_candidate 09988.HK", "suggested_position_pct": 0.75},
            metadata={
                "ticker": "09988.HK",
                "promotion_mode": "reduced_size_pending",
                "position_policy": "reduced_size",
                "optional_warnings": ["capex", "free_cash_flow"],
                "bear_case_gate": {"overall_status": "partially_mitigated"},
            },
        )

        payload = build_ops_payload(conn, "ai_core")

        self.assertEqual(payload["summary"]["pending_human_review"], 1)
        self.assertIn("00700.HK", payload["summary"]["core_blocker_tickers"])
        self.assertIn("002230.SZ", payload["summary"]["unknown_thesis_tickers"])
        self.assertFalse(payload["paper_order_guard"][0]["paper_order_allowed"])


if __name__ == "__main__":
    unittest.main()
