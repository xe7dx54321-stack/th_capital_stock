import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_paper_portfolio_summary import dedupe_reduced_size_rows, pending_candidate_rows, projected_reduced_size_exposure
from smr_decision import ensure_decision_tables, upsert_decision_ledger
from smr_paper_portfolio import ensure_paper_portfolio_tables


class Phase14PortfolioRiskReducedSizeTests(unittest.TestCase):
    def test_reduced_size_pending_is_projected_not_current_exposure(self):
        conn = sqlite3.connect(":memory:")
        ensure_decision_tables(conn)
        ensure_paper_portfolio_tables(conn)
        upsert_decision_ledger(
            conn,
            "phase14-09988",
            "pending_human_review",
            dashboard_summary={"action": "small_candidate 09988.HK", "ticker": "09988.HK", "suggested_position_pct": 0.75},
            metadata={
                "ticker": "09988.HK",
                "market": "H",
                "theme": "china_internet",
                "promotion_mode": "reduced_size_pending",
                "position_policy": "reduced_size",
                "portfolio_risk": {
                    "recommended_position_pct": 0.75,
                    "base_position_pct": 1.5,
                    "market": "H",
                    "theme": "china_internet",
                    "sector": "internet_platform",
                },
            },
        )
        rows = pending_candidate_rows(conn, {"09988.HK": {"market": "H", "theme": "china_internet", "sector": "internet_platform"}})
        reduced = [row for row in rows if row["promotion_mode"] == "reduced_size_pending"]
        projected = projected_reduced_size_exposure(0.0, {"market": {}, "theme": {}, "sector": {}}, reduced)

        self.assertEqual(len(reduced), 1)
        self.assertEqual(reduced[0]["risk_adjusted_position_pct"], 0.75)
        self.assertEqual(reduced[0]["full_size_position_pct"], 1.5)
        self.assertFalse(reduced[0]["auto_approval_allowed"])
        self.assertFalse(reduced[0]["paper_order_allowed"])
        self.assertEqual(projected["total"], 0.75)
        self.assertEqual(projected["market"]["H"], 0.75)

    def test_reduced_size_projection_dedupes_same_ticker(self):
        rows = dedupe_reduced_size_rows(
            [
                {"ticker": "09988.HK", "recommendation_id": "phase13_core_gate__09988.HK__valuation_rerating"},
                {"ticker": "09988.HK", "recommendation_id": "phase14_thesis_aware__09988.HK__valuation_rerating"},
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["recommendation_id"].startswith("phase14_"))


if __name__ == "__main__":
    unittest.main()
