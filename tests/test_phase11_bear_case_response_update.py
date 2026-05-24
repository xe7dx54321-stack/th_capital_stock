import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_bear_case_response import respond_to_bear_case


class Phase11BearCaseResponseUpdateTests(unittest.TestCase):
    def test_valuation_support_partially_mitigates_rerating_bear_case(self):
        response = respond_to_bear_case(
            "09988.HK",
            {"bear_case_claims": [{"claim_text": "valuation rerating lacks support", "severity": "high"}]},
            valuation_snapshot={
                "allowed_usage": "supporting_evidence",
                "generated_at": "2026-05-24 12:00:00",
                "peer_comparison": {"peer_comparison_status": "supporting"},
                "historical_valuation": {"status": "available"},
            },
        )

        self.assertEqual(response["overall_response_status"], "partially_mitigated")
        self.assertEqual(response["action_effect"], "reduce_position_size")
        self.assertTrue(response["responses"][0]["response_evidence_ids"])

    def test_missing_valuation_support_stays_unresolved(self):
        response = respond_to_bear_case(
            "09988.HK",
            {"bear_case_claims": [{"claim_text": "valuation rerating lacks support", "severity": "high"}]},
            valuation_snapshot={"allowed_usage": "supporting_evidence"},
        )

        self.assertEqual(response["overall_response_status"], "unresolved")


if __name__ == "__main__":
    unittest.main()
