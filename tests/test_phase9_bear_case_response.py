import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_bear_case_response import attach_bear_case_response, respond_to_bear_case
from smr_recommendation_promotion import bear_case_requirements


class Phase9BearCaseResponseTests(unittest.TestCase):
    def test_unresolved_high_bear_case_blocks_pending(self):
        bear_case = {"bear_case_strength": "high", "bear_case_claims": [{"claim_text": "valuation unsupported", "severity": "high"}], "deal_breakers": ["risk"]}
        response = respond_to_bear_case("09988.HK", bear_case, evidence_rows=[], valuation_snapshot={"allowed_usage": "context_only"})
        updated = attach_bear_case_response(bear_case, response)
        _, missing, _ = bear_case_requirements(updated, "buy 09988.HK")

        self.assertEqual(response["overall_response_status"], "unresolved")
        self.assertIn("high_bear_case_unresolved", missing)

    def test_partially_mitigated_high_bear_case_still_not_pending(self):
        bear_case = {"bear_case_strength": "high", "bear_case_claims": [{"claim_text": "data risk", "severity": "medium"}], "deal_breakers": ["risk"]}
        response = respond_to_bear_case(
            "09988.HK",
            bear_case,
            evidence_rows=[{"evidence_id": "ev-1", "source_type": "filing", "usable_for_promotion": True, "quality_score": 0.7, "metadata": {"live": True}}],
            fundamentals_snapshot={"missing_fields": ["capex", "free_cash_flow"]},
            valuation_snapshot={"allowed_usage": "supporting_evidence"},
        )
        updated = attach_bear_case_response(bear_case, response)
        _, missing, _ = bear_case_requirements(updated, "buy 09988.HK")

        self.assertEqual(response["overall_response_status"], "partially_mitigated")
        self.assertIn("high_bear_case_partially_mitigated", missing)

    def test_mitigated_high_bear_case_has_thesis_response(self):
        bear_case = {"bear_case_strength": "high", "bear_case_claims": [{"claim_text": "risk", "severity": "medium"}], "deal_breakers": ["risk"]}
        response = respond_to_bear_case(
            "09988.HK",
            bear_case,
            evidence_rows=[
                {"evidence_id": "ev-1", "source_type": "filing", "usable_for_promotion": True, "quality_score": 0.72, "metadata": {"live": True}},
                {"evidence_id": "ev-2", "source_type": "news", "usable_for_promotion": True, "quality_score": 0.7, "metadata": {"live": True}},
            ],
            fundamentals_snapshot={"missing_fields": []},
            valuation_snapshot={"allowed_usage": "supporting_evidence"},
        )
        updated = attach_bear_case_response(bear_case, response)
        _, missing, _ = bear_case_requirements(updated, "buy 09988.HK")

        self.assertEqual(response["overall_response_status"], "mitigated")
        self.assertNotIn("high_bear_case_unresolved", missing)
        self.assertTrue(updated.get("thesis_response"))


if __name__ == "__main__":
    unittest.main()
