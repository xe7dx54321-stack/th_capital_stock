import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_bear_case_response import respond_to_bear_case


class Phase10BearCaseResponseV2Tests(unittest.TestCase):
    def test_response_summary_counts_statuses(self):
        response = respond_to_bear_case(
            "09988.HK",
            {"bear_case_claims": [{"claim_text": "growth uncertainty remains high", "severity": "high"}]},
            evidence_rows=[{"evidence_id": "ev-1", "source_type": "filing", "usable_for_promotion": True, "quality_score": 0.7, "metadata": {"live": True}}],
            fundamentals_snapshot={"missing_fields": ["capex", "free_cash_flow", "gross_profit"]},
            valuation_snapshot={"allowed_usage": "supporting_evidence"},
        )

        self.assertIn("bear_case_response_summary", response)
        self.assertEqual(response["bear_case_response_summary"]["overall_status"], "partially_mitigated")
        self.assertEqual(response["action_effect"], "reduce_position_size")

    def test_core_valuation_bear_case_remains_unresolved_when_valuation_blocked(self):
        response = respond_to_bear_case(
            "09988.HK",
            {"bear_case_claims": [{"claim_text": "valuation rerating lacks support", "severity": "high"}]},
            evidence_rows=[{"evidence_id": "ev-1", "source_type": "filing", "usable_for_promotion": True, "quality_score": 0.7, "metadata": {"live": True}}],
            fundamentals_snapshot={"missing_fields": []},
            valuation_snapshot={"allowed_usage": "blocked_due_to_stale_price"},
        )

        self.assertEqual(response["overall_response_status"], "unresolved")
        self.assertEqual(response["action_effect"], "block_pending_review")


if __name__ == "__main__":
    unittest.main()
