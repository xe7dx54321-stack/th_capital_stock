import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_decision import review_recommendation, upsert_decision_ledger
from smr_paper_portfolio import apply_approved_recommendations, create_order_for_approved_recommendation


def make_conn():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE daily_bar (ts_code TEXT, market TEXT, trade_date TEXT, close REAL);
        CREATE TABLE us_daily_bar (symbol TEXT, trade_date TEXT, close REAL);
        """
    )
    return conn


class Phase15PaperOrderGuardTests(unittest.TestCase):
    def seed_price(self, conn):
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO daily_bar VALUES ('09988.HK', 'H', ?, 80.0)", (today,))

    def seed_pending(self, conn, rec_id="rec-09988", pct=0.75):
        upsert_decision_ledger(
            conn,
            rec_id,
            "pending_human_review",
            dashboard_summary={"action": "small_candidate 09988.HK", "suggested_position_pct": pct, "max_position_pct": 1.0},
            metadata={"ticker": "09988.HK", "market": "H", "promotion_mode": "reduced_size_pending"},
        )

    def test_pending_reduced_size_does_not_create_order(self):
        conn = make_conn()
        self.seed_price(conn)
        self.seed_pending(conn)

        result = create_order_for_approved_recommendation(
            conn,
            {"recommendation_id": "rec-09988", "ticker": "09988.HK", "market": "H", "action": "small_candidate", "suggested_position_pct": 0.75},
        )

        self.assertEqual(result["status"], "blocked_not_approved")
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM paper_portfolio_orders").fetchone()[0], 0)

    def test_approved_paper_creates_order_and_position(self):
        conn = make_conn()
        self.seed_price(conn)
        self.seed_pending(conn)
        review_recommendation(conn, "rec-09988", "tester", "approve_paper", "approve")

        result = apply_approved_recommendations(conn)

        self.assertEqual(result["orders_created"], 1)
        self.assertEqual(result["positions_opened"], 1)

    def test_reduce_then_approve_uses_adjusted_position_pct(self):
        conn = make_conn()
        self.seed_price(conn)
        self.seed_pending(conn, pct=0.75)
        review_recommendation(conn, "rec-09988", "tester", "reduce_position_size", "lower", {"new_position_pct": 0.5})
        review_recommendation(conn, "rec-09988", "tester", "approve_paper", "approve after reduce")

        result = apply_approved_recommendations(conn)

        self.assertEqual(result["positions_opened"], 1)
        position_pct = conn.execute("SELECT position_pct FROM paper_portfolio_positions WHERE source_recommendation_id='rec-09988'").fetchone()[0]
        self.assertEqual(position_pct, 0.5)

    def test_rejected_does_not_create_order(self):
        conn = make_conn()
        self.seed_price(conn)
        self.seed_pending(conn)
        review_recommendation(conn, "rec-09988", "tester", "reject", "reject")

        result = apply_approved_recommendations(conn)

        self.assertEqual(result["approved_seen"], 0)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM paper_portfolio_orders").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
