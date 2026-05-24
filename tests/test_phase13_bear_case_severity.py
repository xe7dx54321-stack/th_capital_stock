import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_bear_case_response import respond_to_bear_case


class Phase13BearCaseSeverityTests(unittest.TestCase):
    def test_non_core_partially_mitigated_bear_case_allows_reduced_size(self):
        response = respond_to_bear_case(
            "09988.HK",
            {"bear_case_claims": [{"claim_id": "bear_quality", "claim_text": "fundamentals data quality remains weak", "severity": "high"}]},
            thesis_types=["valuation_rerating"],
            field_gate={"core_blockers": [], "optional_warnings": [{"field": "capex"}]},
            data_quality_gate={"status": "degraded_non_core"},
            fundamentals_snapshot={
                "field_details": {
                    f"field_{idx}": {"allowed_usage": "supporting_evidence", "source_evidence_id": f"ev_{idx}"}
                    for idx in range(5)
                }
            },
        )

        first = response["responses"][0]
        self.assertFalse(first["core_to_thesis"])
        self.assertEqual(first["risk_category"], "data_quality_bear_case")
        self.assertEqual(first["residual_risk_level"], "medium")
        self.assertEqual(response["action_effect"], "reduced_size_candidate_allowed")

    def test_unresolved_core_bear_case_blocks_pending(self):
        response = respond_to_bear_case(
            "09988.HK",
            {"bear_case_claims": [{"claim_id": "bear_quality", "claim_text": "fundamentals data quality remains weak", "severity": "high"}]},
            thesis_types=["cash_flow_improvement"],
            field_gate={"core_blockers": [{"field": "capex"}, {"field": "free_cash_flow"}]},
            data_quality_gate={"status": "degraded_core"},
            fundamentals_snapshot={"field_details": {}},
        )

        first = response["responses"][0]
        self.assertTrue(first["core_to_thesis"])
        self.assertEqual(first["response_status"], "unresolved")
        self.assertEqual(first["residual_risk_level"], "critical")
        self.assertEqual(response["action_effect"], "block_pending_review")


if __name__ == "__main__":
    unittest.main()
