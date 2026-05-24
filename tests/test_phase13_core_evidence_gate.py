import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

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


class Phase13CoreEvidenceGateTests(unittest.TestCase):
    def test_optional_missing_is_warning_not_core_blocker(self):
        gate = build_promotion_evidence_gate(
            ticker="09988.HK",
            thesis_types=["valuation_rerating"],
            missing_fields=["capex", "free_cash_flow"],
            field_details={"capex": {"missing_reason": "field_not_found"}},
        )

        self.assertEqual(gate["gate_status"], "pass_with_warnings")
        self.assertEqual([item["field"] for item in gate["optional_warnings"]], ["capex", "free_cash_flow"])
        self.assertEqual(gate["core_blockers"], [])

    def test_core_missing_blocks_promotion(self):
        gate = build_promotion_evidence_gate(
            ticker="09988.HK",
            thesis_types=["cash_flow_improvement"],
            missing_fields=["capex", "free_cash_flow"],
            field_details={},
        )
        result = evaluate_promotion(
            dashboard_summary={"action": "small_candidate 09988.HK", "ticker": "09988.HK", "suggested_position_pct": 1.0, "max_position_pct": 1.0},
            data_health_snapshot=passing_health(),
            evidence_check_snapshot={"severity": "pass", "evidence_summary": {"source_path_count": 2, "primary_anchor_count": 1}},
            claim_graph_snapshot={"unsupported_core_claims": [], "counter_evidence_count": 1},
            valuation_snapshot={"allowed_usage": "supporting_evidence"},
            fundamentals_snapshot={"freshness_status": "degraded", "missing_fields": ["capex", "free_cash_flow"]},
            consensus_proxy={"proxy_quality": "strong", "usable_for_promotion": True, "is_official_consensus": False},
            bear_case={"bear_case_claims": [{"claim_text": "risk"}], "deal_breakers": ["break"]},
            risk_snapshot={"status": "pass"},
            lint_result={"max_severity": "info", "issues": []},
            promotion_evidence_gate=gate,
        )

        self.assertFalse(result.allowed)
        self.assertIn("core_evidence_blocker", result.missing_requirements)

    def test_optional_missing_does_not_create_missing_requirement(self):
        gate = build_promotion_evidence_gate(
            ticker="09988.HK",
            thesis_types=["valuation_rerating"],
            missing_fields=["capex"],
            field_details={},
        )
        result = evaluate_promotion(
            dashboard_summary={"action": "small_candidate 09988.HK", "ticker": "09988.HK", "suggested_position_pct": 1.0, "max_position_pct": 1.0},
            data_health_snapshot=passing_health(),
            evidence_check_snapshot={"severity": "pass", "evidence_summary": {"source_path_count": 2, "primary_anchor_count": 1}},
            claim_graph_snapshot={"unsupported_core_claims": [], "counter_evidence_count": 1},
            valuation_snapshot={"allowed_usage": "supporting_evidence"},
            fundamentals_snapshot={"freshness_status": "degraded", "missing_fields": ["capex"]},
            consensus_proxy={"proxy_quality": "medium", "usable_for_promotion": True, "is_official_consensus": False},
            bear_case={"bear_case_claims": [{"claim_text": "risk"}], "deal_breakers": ["break"]},
            risk_snapshot={"status": "pass"},
            lint_result={"max_severity": "info", "issues": []},
            promotion_evidence_gate=gate,
            reduced_size_policy={"default_multiplier": 0.5, "max_reduced_size_pct": 1.0},
        )

        self.assertTrue(result.allowed)
        self.assertNotIn("core_evidence_blocker", result.missing_requirements)
        self.assertEqual(result.snapshots["promotion_mode"], "reduced_size_pending")


if __name__ == "__main__":
    unittest.main()
