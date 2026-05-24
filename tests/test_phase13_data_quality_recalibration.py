import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_data_quality_gate import build_data_quality_gate


class Phase13DataQualityRecalibrationTests(unittest.TestCase):
    def test_optional_missing_fields_become_degraded_non_core(self):
        gate = build_data_quality_gate(
            ticker="09988.HK",
            thesis_types=["valuation_rerating"],
            root_causes=["FIELD_NOT_FOUND:capex", "FIELD_NOT_FOUND:free_cash_flow"],
            field_quality={
                "capex": {"status": "missing", "missing_reason": "field_not_found"},
                "free_cash_flow": {"status": "missing", "missing_reason": "derived_field_missing_inputs"},
            },
            before_status="degraded",
        )

        self.assertEqual(gate["status"], "degraded_non_core")
        self.assertFalse(gate["promotion_blocking"])
        self.assertEqual([item["field"] for item in gate["non_core_issues"]], ["capex", "free_cash_flow"])

    def test_core_missing_fields_remain_blocking(self):
        gate = build_data_quality_gate(
            ticker="09988.HK",
            thesis_types=["cash_flow_improvement"],
            root_causes=["FIELD_NOT_FOUND:capex", "FIELD_NOT_FOUND:free_cash_flow"],
            field_quality={},
            before_status="degraded",
        )

        self.assertEqual(gate["status"], "degraded_core")
        self.assertTrue(gate["promotion_blocking"])
        self.assertEqual([item["field"] for item in gate["core_issues"]], ["capex", "free_cash_flow"])


if __name__ == "__main__":
    unittest.main()
