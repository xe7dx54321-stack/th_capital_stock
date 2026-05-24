import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from validate_phase13_core_gate_repaired_candidate import build_phase13_gates


class Phase1309988RevalidationTests(unittest.TestCase):
    def test_valuation_revalidation_gate_reports_before_after_shape(self):
        field_gate, data_quality_gate = build_phase13_gates(
            "09988.HK",
            ["valuation_rerating"],
            {
                "after": {
                    "data_quality_status": "degraded",
                    "root_causes": ["FIELD_NOT_FOUND:capex", "FIELD_NOT_FOUND:free_cash_flow"],
                },
                "after_field_quality": {
                    "capex": {"status": "missing", "missing_reason": "field_not_found"},
                    "free_cash_flow": {"status": "missing", "missing_reason": "derived_field_missing_inputs"},
                },
            },
        )

        self.assertEqual(field_gate["gate_status"], "pass_with_warnings")
        self.assertEqual([item["field"] for item in field_gate["optional_warnings"]], ["capex", "free_cash_flow"])
        self.assertEqual(data_quality_gate["before_status"], "degraded")
        self.assertEqual(data_quality_gate["after_status"], "degraded_non_core")

    def test_cash_flow_revalidation_gate_keeps_core_blockers(self):
        field_gate, data_quality_gate = build_phase13_gates(
            "09988.HK",
            ["cash_flow_improvement"],
            {
                "after": {
                    "data_quality_status": "degraded",
                    "root_causes": ["FIELD_NOT_FOUND:capex", "FIELD_NOT_FOUND:free_cash_flow"],
                },
                "after_field_quality": {},
            },
        )

        self.assertEqual([item["field"] for item in field_gate["core_blockers"]], ["capex", "free_cash_flow"])
        self.assertEqual(data_quality_gate["status"], "degraded_core")


if __name__ == "__main__":
    unittest.main()
