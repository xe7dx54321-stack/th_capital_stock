import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_claim_graph import ensure_claim_graph_tables
from smr_data_health import ensure_data_health_tables
from smr_decision import current_decision_status
from smr_recommendation_promotion import evaluate_promotion


def memory_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    ensure_data_health_tables(conn)
    ensure_claim_graph_tables(conn)
    return conn


def passing_health() -> dict:
    return {
        "overall_status": "fresh",
        "items": [
            {"data_type": "daily_bar", "market": "A", "freshness_status": "fresh", "blocking_level": "none"},
            {"data_type": "daily_bar", "market": "H", "freshness_status": "fresh", "blocking_level": "none"},
            {"data_type": "daily_bar", "market": "US", "freshness_status": "fresh", "blocking_level": "none"},
            {"data_type": "news", "market": "US", "freshness_status": "fresh", "blocking_level": "none"},
            {
                "data_type": "filings",
                "market": "US",
                "freshness_status": "fresh",
                "blocking_level": "none",
                "metadata": {"scope": "watchlist", "ticker": "NVDA"},
            },
        ],
    }


class RecommendationPromotionTests(unittest.TestCase):
    def test_missing_requirements_are_machine_readable(self):
        result = evaluate_promotion(
            dashboard_summary={"action": "buy NVDA", "ticker": "NVDA"},
            data_health_snapshot={"items": []},
            evidence_check_snapshot={},
            claim_graph_snapshot={},
            valuation_snapshot={"allowed_usage": "context_only"},
            consensus_proxy={"proxy_quality": "weak"},
            bear_case={},
            lint_result={"max_severity": "info", "issues": []},
        )

        self.assertFalse(result.allowed)
        self.assertIn("data_health_snapshot", result.missing_requirements)
        self.assertIn("valuation_not_context_only_for_buy_add", result.missing_requirements)
        self.assertTrue(result.required_fixes)

    def test_success_promotes_and_writes_ledger(self):
        conn = memory_conn()
        result = evaluate_promotion(
            conn,
            report_id="report-promo",
            recommendation_id="rec-promo",
            dashboard_summary={
                "action": "buy NVDA",
                "ticker": "NVDA",
                "suggested_position_pct": 2.0,
                "max_position_pct": 5.0,
            },
            data_health_snapshot=passing_health(),
            evidence_check_snapshot={"severity": "pass", "evidence_summary": {"source_path_count": 2, "primary_anchor_count": 1}},
            claim_graph_snapshot={"unsupported_core_claims": [], "counter_evidence_count": 1},
            valuation_snapshot={"allowed_usage": "supporting_evidence"},
            consensus_proxy={"proxy_quality": "strong", "usable_for_promotion": True, "is_official_consensus": False},
            bear_case={"bear_case_claims": [{"claim_text": "risk"}], "deal_breakers": ["break"]},
            risk_snapshot={"status": "pass"},
            lint_result={"max_severity": "info", "issues": []},
            write_ledger=True,
        )

        self.assertTrue(result.allowed)
        self.assertEqual(result.to_status, "pending_human_review")
        self.assertEqual(current_decision_status(conn, "rec-promo"), "pending_human_review")


if __name__ == "__main__":
    unittest.main()
