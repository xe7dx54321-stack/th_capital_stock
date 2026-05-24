import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_decision import current_decision_status
from smr_recommendation_candidate import build_recommendation_candidate
from smr_recommendation_promotion import evaluate_promotion
from smr_thesis_dependency import build_promotion_evidence_gate


def passing_health():
    return {
        "items": [
            {"data_type": "daily_bar", "market": "H", "freshness_status": "fresh", "blocking_level": "none"},
            {"data_type": "news", "market": "H", "freshness_status": "fresh", "blocking_level": "none"},
            {"data_type": "filings", "market": "H", "freshness_status": "fresh", "blocking_level": "none", "metadata": {"ticker": "09988.HK"}},
        ]
    }


class Phase13ReducedSizePendingTests(unittest.TestCase):
    def test_reduced_size_pending_writes_decision_ledger(self):
        conn = sqlite3.connect(":memory:")
        field_gate = build_promotion_evidence_gate(
            ticker="09988.HK",
            thesis_types=["valuation_rerating"],
            missing_fields=["capex", "free_cash_flow"],
            field_details={},
        )
        bear_gate = {
            "overall_status": "partially_mitigated",
            "residual_risk_level": "medium",
            "action_effect": "reduced_size_candidate_allowed",
            "has_critical_unresolved_core_risk": False,
            "gate_status": "reduced_size_allowed",
        }
        promotion = evaluate_promotion(
            conn,
            report_id="phase13-test",
            recommendation_id="phase13-rec",
            dashboard_summary={"action": "small_candidate 09988.HK", "ticker": "09988.HK", "suggested_position_pct": 1.5, "max_position_pct": 3.0},
            data_health_snapshot=passing_health(),
            evidence_check_snapshot={"severity": "pass", "evidence_summary": {"source_path_count": 2, "primary_anchor_count": 1}},
            claim_graph_snapshot={"unsupported_core_claims": [], "counter_evidence_count": 1},
            valuation_snapshot={"allowed_usage": "supporting_evidence"},
            fundamentals_snapshot={"freshness_status": "degraded", "missing_fields": ["capex", "free_cash_flow"]},
            consensus_proxy={"proxy_quality": "medium", "usable_for_promotion": True, "is_official_consensus": False},
            bear_case={
                "bear_case_strength": "high",
                "bear_case_claims": [{"claim_text": "risk"}],
                "deal_breakers": ["break"],
                "bear_case_response": {"overall_response_status": "partially_mitigated"},
                "bear_case_gate": bear_gate,
                "data_quality_gate": {"status": "degraded_non_core"},
                "data_quality_risk": "high",
            },
            risk_snapshot={"status": "pass"},
            lint_result={"max_severity": "info", "issues": []},
            thesis_types=["valuation_rerating"],
            promotion_evidence_gate=field_gate,
            data_quality_gate={"status": "degraded_non_core"},
            bear_case_gate=bear_gate,
            reduced_size_policy={"default_multiplier": 0.5, "max_reduced_size_pct": 1.0},
            write_ledger=True,
        )
        candidate = build_recommendation_candidate(
            conn,
            recommendation_id="phase13-rec",
            ticker="09988.HK",
            report={"action": "small_candidate 09988.HK", "kill_triggers": ["break"]},
            valuation_snapshot={"allowed_usage": "supporting_evidence"},
            consensus_proxy={"proxy_quality": "medium", "usable_for_promotion": True},
            bear_case={"bear_case_strength": "high", "deal_breakers": ["break"]},
            risk_snapshot={"status": "pass"},
            portfolio_risk={"status": "pass", "recommended_position_pct": 0.75, "recommended_max_position_pct": 1.0},
            market_signal={"signal": "positive"},
            promotion_result=promotion,
            write_ledger=True,
        )

        self.assertTrue(promotion.allowed)
        self.assertEqual(candidate["status"], "pending_human_review")
        self.assertEqual(candidate["action"], "small_candidate")
        self.assertEqual(candidate["position_policy"], "reduced_size")
        self.assertEqual(candidate["suggested_position_pct"], 0.75)
        self.assertEqual(current_decision_status(conn, "phase13-rec"), "pending_human_review")


if __name__ == "__main__":
    unittest.main()
