import sqlite3
import sys
import unittest
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_decision import upsert_decision_ledger
from validate_phase15_review_to_paper_smoke import validate_smoke


class Phase15ReviewToPaperSmokeTests(unittest.TestCase):
    def make_conn(self):
        conn = sqlite3.connect(":memory:")
        conn.executescript(
            """
            CREATE TABLE daily_bar (ts_code TEXT, market TEXT, trade_date TEXT, close REAL);
            CREATE TABLE us_daily_bar (symbol TEXT, trade_date TEXT, close REAL);
            """
        )
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO daily_bar VALUES ('09988.HK', 'H', ?, 80.0)", (today,))
        upsert_decision_ledger(
            conn,
            "phase14_thesis_aware__09988.HK__valuation_rerating",
            "pending_human_review",
            dashboard_summary={"action": "small_candidate 09988.HK", "suggested_position_pct": 0.75, "max_position_pct": 1.0},
            metadata={
                "ticker": "09988.HK",
                "market": "H",
                "promotion_mode": "reduced_size_pending",
                "position_policy": "reduced_size",
                "thesis_inference": {"primary_thesis_type": "valuation_rerating", "confidence": 0.72},
            },
        )
        conn.commit()
        return conn

    def test_dry_run_validates_manual_approval_without_writes(self):
        conn = self.make_conn()

        result = validate_smoke(conn, "09988.HK", execute=False)

        self.assertTrue(result["stages"]["reduced_size_pending_found"])
        self.assertTrue(result["stages"]["paper_order_blocked_before_approval"])
        self.assertTrue(result["stages"]["manual_approval_dry_run"])
        self.assertTrue(result["would_create_order"])
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM paper_portfolio_orders").fetchone()[0], 0)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM human_review_actions").fetchone()[0], 0)
        metadata_raw = conn.execute(
            "SELECT metadata_json FROM decision_ledger WHERE recommendation_id=? ORDER BY id DESC LIMIT 1",
            ("phase14_thesis_aware__09988.HK__valuation_rerating",),
        ).fetchone()[0]
        self.assertNotIn("paper_portfolio", json.loads(metadata_raw))


if __name__ == "__main__":
    unittest.main()
