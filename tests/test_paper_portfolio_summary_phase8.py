import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_paper_portfolio_summary import _add_exposure_maps, _exposure_warnings, pending_candidate_rows
from smr_decision import ensure_decision_tables, upsert_decision_ledger
from smr_paper_portfolio import ensure_paper_portfolio_tables


class PaperPortfolioSummaryPhase8Tests(unittest.TestCase):
    def make_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        ensure_decision_tables(conn)
        ensure_paper_portfolio_tables(conn)
        return conn

    def test_pending_candidate_rows_and_projected_exposure(self):
        conn = self.make_conn()
        upsert_decision_ledger(
            conn,
            "phase6_live__NVDA",
            "candidate_shadow",
            dashboard_summary={"action": "small_candidate", "ticker": "NVDA", "suggested_position_pct": 2.0, "max_position_pct": 2.5},
            metadata={
                "ticker": "NVDA",
                "market": "US",
                "candidate": {"theme": "semiconductor_compute", "sector": "semiconductor_compute"},
                "portfolio_risk": {"recommended_position_pct": 1.0, "theme": "semiconductor_compute", "sector": "semiconductor_compute", "market": "US"},
            },
        )
        watchlist = {"NVDA": {"ticker": "NVDA", "market": "US", "theme": "semiconductor_compute", "sector": "semiconductor_compute"}}

        rows = pending_candidate_rows(conn, watchlist)
        projected = _add_exposure_maps({"theme": {"semiconductor_compute": 11.5}, "market": {"US": 4.0}, "sector": {"semiconductor_compute": 11.5}}, rows)
        adjusted = _add_exposure_maps({"theme": {"semiconductor_compute": 11.5}, "market": {"US": 4.0}, "sector": {"semiconductor_compute": 11.5}}, rows, "risk_adjusted_position_pct")
        warnings = _exposure_warnings(projected)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["risk_adjusted_position_pct"], 1.0)
        self.assertGreater(projected["theme"]["semiconductor_compute"], adjusted["theme"]["semiconductor_compute"])
        self.assertTrue(any(item["code"] == "THEME_EXPOSURE_LIMIT" for item in warnings))


if __name__ == "__main__":
    unittest.main()
