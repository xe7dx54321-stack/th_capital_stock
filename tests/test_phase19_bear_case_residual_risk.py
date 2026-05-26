import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_bear_case_response import decompose_bear_case_residual_risk


class Phase19BearCaseResidualRiskTests(unittest.TestCase):
    def test_unresolved_high_core_bear_case_blocks_pending(self):
        payload = decompose_bear_case_residual_risk(
            "300308.SZ",
            {"overall_status": "unresolved", "residual_risk_level": "high", "action_effect": "block_pending_review"},
        )

        gate = payload["bear_case_residual_risk"]
        self.assertTrue(gate["blocks_pending"])
        self.assertFalse(gate["allows_reduced_size_pending"])

    def test_partially_mitigated_medium_allows_reduced_size_pending(self):
        payload = decompose_bear_case_residual_risk(
            "09988.HK",
            {"overall_status": "partially_mitigated", "residual_risk_level": "medium", "action_effect": "reduce_position_size"},
        )

        gate = payload["bear_case_residual_risk"]
        self.assertFalse(gate["blocks_pending"])
        self.assertTrue(gate["allows_reduced_size_pending"])


if __name__ == "__main__":
    unittest.main()
