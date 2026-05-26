import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_supply_chain_theme_template import get_supply_chain_template, validate_supply_chain_template


class Phase25SupplyChainThemeTemplateTests(unittest.TestCase):
    def test_ai_optical_interconnect_template_is_valid(self):
        template = get_supply_chain_template("ai_optical_interconnect")
        self.assertEqual(template["status"], "available")
        self.assertIn("end_demand_drivers", template)
        self.assertIn("product_layers", template)
        self.assertIn("supplier_variables", template)
        self.assertIn("expectation_variables", template)
        self.assertEqual(validate_supply_chain_template(template), [])


if __name__ == "__main__":
    unittest.main()
