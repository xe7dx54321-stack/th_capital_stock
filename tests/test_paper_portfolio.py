import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from smr_decision import review_recommendation, upsert_decision_ledger
from smr_paper_portfolio import apply_approved_recommendations, mark_open_positions_to_market

import validate_phase5_paper_portfolio_smoke as paper_smoke


def make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE us_daily_bar (
            symbol TEXT,
            trade_date TEXT,
            close REAL
        );
        CREATE TABLE daily_bar (
            ts_code TEXT,
            market TEXT,
            trade_date TEXT,
            close REAL
        );
        """
    )
    return conn


class PaperPortfolioTests(unittest.TestCase):
    def test_pending_review_does_not_create_order(self):
        conn = make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO us_daily_bar VALUES ('NVDA', ?, 100.0)", (today,))
        upsert_decision_ledger(
            conn,
            "rec-pending",
            "pending_human_review",
            dashboard_summary={"action": "buy NVDA", "suggested_position_pct": 2.0, "max_position_pct": 5.0},
        )

        result = apply_approved_recommendations(conn)

        self.assertEqual(result["approved_seen"], 0)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM paper_portfolio_orders").fetchone()[0], 0)

    def test_approved_paper_creates_order_and_open_position(self):
        conn = make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO us_daily_bar VALUES ('NVDA', ?, 100.0)", (today,))
        upsert_decision_ledger(
            conn,
            "rec-approved",
            "pending_human_review",
            dashboard_summary={"action": "buy NVDA", "suggested_position_pct": 2.0, "max_position_pct": 5.0},
        )
        review_recommendation(conn, "rec-approved", "tester", "approve_paper", "approved for paper trading")

        result = apply_approved_recommendations(conn)

        self.assertEqual(result["approved_seen"], 1)
        self.assertEqual(result["orders_created"], 1)
        self.assertEqual(result["positions_opened"], 1)
        order_status = conn.execute("SELECT status FROM paper_portfolio_orders WHERE recommendation_id='rec-approved'").fetchone()[0]
        position_status = conn.execute("SELECT status FROM paper_portfolio_positions WHERE source_recommendation_id='rec-approved'").fetchone()[0]
        self.assertEqual(order_status, "executed")
        self.assertEqual(position_status, "open")
        metadata = conn.execute("SELECT metadata_json FROM decision_ledger WHERE recommendation_id='rec-approved'").fetchone()[0]
        self.assertIn("paper_position_open", metadata)

    def test_stale_price_blocks_execution(self):
        conn = make_conn()
        conn.execute("INSERT INTO us_daily_bar VALUES ('NVDA', '2000-01-01', 100.0)")
        upsert_decision_ledger(
            conn,
            "rec-stale",
            "approved_paper",
            dashboard_summary={"action": "buy NVDA", "suggested_position_pct": 2.0, "max_position_pct": 5.0},
        )

        result = apply_approved_recommendations(conn, max_price_age_days=1)

        self.assertEqual(result["orders_created"], 1)
        self.assertEqual(result["positions_opened"], 0)
        order_status = conn.execute("SELECT status FROM paper_portfolio_orders WHERE recommendation_id='rec-stale'").fetchone()[0]
        self.assertEqual(order_status, "blocked_stale_price")

    def test_mark_open_positions_to_market_updates_metadata(self):
        conn = make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO us_daily_bar VALUES ('NVDA', ?, 100.0)", (today,))
        upsert_decision_ledger(
            conn,
            "rec-mark",
            "approved_paper",
            dashboard_summary={"action": "buy NVDA", "suggested_position_pct": 1.0, "max_position_pct": 3.0},
        )
        apply_approved_recommendations(conn)
        conn.execute("INSERT INTO us_daily_bar VALUES ('NVDA', ?, 110.0)", (today,))

        result = mark_open_positions_to_market(conn)

        self.assertEqual(result["paper_positions_marked"], 1)
        metadata = conn.execute("SELECT metadata_json FROM paper_portfolio_positions WHERE source_recommendation_id='rec-mark'").fetchone()[0]
        self.assertIn("mark_to_market", metadata)

    def test_smoke_accepts_traceable_chain_after_replay_pending_status(self):
        conn = make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO us_daily_bar VALUES ('NVDA', ?, 100.0)", (today,))
        upsert_decision_ledger(
            conn,
            "rec-replayed",
            "pending_human_review",
            dashboard_summary={"action": "buy NVDA", "suggested_position_pct": 2.0, "max_position_pct": 5.0},
        )
        review_recommendation(conn, "rec-replayed", "tester", "approve_paper", "approved for paper trading")
        apply_approved_recommendations(conn)
        upsert_decision_ledger(
            conn,
            "rec-replayed",
            "pending_human_review",
            dashboard_summary={"action": "buy NVDA", "suggested_position_pct": 2.0, "max_position_pct": 5.0},
        )

        result = paper_smoke.inspect_chain(conn, "rec-replayed")

        self.assertEqual(result["current_status"], "pending_human_review")
        self.assertEqual(result["chain_status"], "complete")
        self.assertEqual(result["missing_stages"], [])


if __name__ == "__main__":
    unittest.main()
