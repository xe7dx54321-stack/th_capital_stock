import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_decision import current_decision_status, ensure_decision_tables, upsert_decision_ledger
from smr_human_review_workflow import apply_human_review_action, get_review_detail


class Phase15HumanReviewWorkflowTests(unittest.TestCase):
    def make_conn(self):
        conn = sqlite3.connect(":memory:")
        ensure_decision_tables(conn)
        return conn

    def seed_pending(self, conn, rec_id="phase14__09988.HK__valuation_rerating"):
        upsert_decision_ledger(
            conn,
            rec_id,
            "pending_human_review",
            dashboard_summary={"action": "small_candidate 09988.HK", "suggested_position_pct": 0.75, "max_position_pct": 1.0},
            metadata={
                "ticker": "09988.HK",
                "promotion_mode": "reduced_size_pending",
                "position_policy": "reduced_size",
                "thesis_inference": {"primary_thesis_type": "valuation_rerating", "confidence": 0.72},
                "promotion_evidence_gate": {"optional_warnings": [{"field": "capex"}]},
            },
        )

    def test_pending_human_review_can_approve_paper_and_logs_action(self):
        conn = self.make_conn()
        self.seed_pending(conn)

        result = apply_human_review_action(
            conn,
            recommendation_id="phase14__09988.HK__valuation_rerating",
            action="approve_paper",
            reviewer="tester",
            note="approve reduced-size paper observation",
            dry_run=False,
        )

        self.assertEqual(result["after_status"], "approved_paper")
        self.assertEqual(current_decision_status(conn, "phase14__09988.HK__valuation_rerating"), "approved_paper")
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM human_review_actions").fetchone()[0], 1)
        detail = get_review_detail(conn, "phase14__09988.HK__valuation_rerating")
        self.assertTrue(detail["paper_order_allowed"])

    def test_non_pending_cannot_approve_paper(self):
        conn = self.make_conn()
        upsert_decision_ledger(conn, "shadow-rec", "candidate_shadow", dashboard_summary={"action": "watch NVDA"})

        dry = apply_human_review_action(
            conn,
            recommendation_id="shadow-rec",
            action="approve_paper",
            reviewer="tester",
            note="should not approve",
            dry_run=True,
        )

        self.assertFalse(dry["allowed"])
        with self.assertRaises(ValueError):
            apply_human_review_action(
                conn,
                recommendation_id="shadow-rec",
                action="approve_paper",
                reviewer="tester",
                note="should not approve",
                dry_run=False,
            )

    def test_review_actions_set_expected_statuses(self):
        actions = {
            "reject": "rejected",
            "downgrade": "candidate_shadow",
            "request_more_research": "needs_more_research",
            "archive": "archived",
        }
        for action, expected in actions.items():
            conn = self.make_conn()
            self.seed_pending(conn, f"rec-{action}")
            result = apply_human_review_action(
                conn,
                recommendation_id=f"rec-{action}",
                action=action,
                reviewer="tester",
                note=f"{action} note",
                dry_run=False,
            )
            self.assertEqual(result["after_status"], expected)

    def test_reduce_position_size_cannot_increase(self):
        conn = self.make_conn()
        self.seed_pending(conn)

        with self.assertRaises(ValueError):
            apply_human_review_action(
                conn,
                recommendation_id="phase14__09988.HK__valuation_rerating",
                action="reduce_position_size",
                reviewer="tester",
                note="bad increase",
                new_position_pct=1.0,
                dry_run=False,
            )
        result = apply_human_review_action(
            conn,
            recommendation_id="phase14__09988.HK__valuation_rerating",
            action="reduce_position_size",
            reviewer="tester",
            note="lower risk",
            new_position_pct=0.5,
            dry_run=False,
        )
        self.assertEqual(result["after_position_pct"], 0.5)


if __name__ == "__main__":
    unittest.main()
