import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_thesis_dependency import classify_missing_fields, get_required_fields_for_thesis, load_thesis_requirements


class Phase13ThesisDependencyTests(unittest.TestCase):
    def test_config_loads_and_contains_phase13_theses(self):
        config = load_thesis_requirements()
        self.assertIn("valuation_rerating", config["thesis_requirements"])
        self.assertIn("cash_flow_improvement", config["thesis_requirements"])

    def test_capex_and_fcf_are_optional_for_valuation_rerating(self):
        result = classify_missing_fields(["capex", "free_cash_flow"], ["valuation_rerating"], {})
        self.assertEqual(result["optional_missing"], ["capex", "free_cash_flow"])
        self.assertEqual(result["core_missing"], [])

    def test_capex_and_fcf_are_core_for_cash_flow_improvement(self):
        result = classify_missing_fields(["capex", "free_cash_flow"], ["cash_flow_improvement"], {})
        self.assertEqual(result["core_missing"], ["capex", "free_cash_flow"])
        self.assertEqual(result["optional_missing"], [])

    def test_core_wins_when_multiple_theses_conflict(self):
        fields = get_required_fields_for_thesis(["valuation_rerating", "cash_flow_improvement"])
        self.assertIn("capex", fields["core_fields"])
        self.assertNotIn("capex", fields["optional_fields"])


if __name__ == "__main__":
    unittest.main()
