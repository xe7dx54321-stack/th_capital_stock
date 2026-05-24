import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_financial_units import normalize_financial_unit


class Phase12UnitNormalizationTests(unittest.TestCase):
    def test_chinese_and_english_amount_units_parse(self):
        cny = normalize_financial_unit("123,456", "人民币百万元", field="revenue", market="H")
        hkd = normalize_financial_unit(12, "HKD thousand", field="cash_and_equivalents", market="H")
        rmb = normalize_financial_unit(10, "RMB million", field="net_income", market="US")

        self.assertEqual(cny["currency"], "CNY")
        self.assertEqual(cny["scale"], 1_000_000.0)
        self.assertEqual(hkd["currency"], "HKD")
        self.assertEqual(hkd["scale"], 1_000.0)
        self.assertEqual(rmb["currency"], "CNY")
        self.assertGreaterEqual(cny["unit_confidence"], 0.9)

    def test_ambiguous_unit_is_blocked(self):
        result = normalize_financial_unit(100, None, field="revenue", market="H")

        self.assertEqual(result["unit_warning"], "ambiguous_unit")
        self.assertEqual(result["allowed_usage"], "blocked")

    def test_eps_and_percentage_are_not_scaled_as_amounts(self):
        eps = normalize_financial_unit(4.2, "HKD/share", field="eps_basic", market="H", context="HKD million")
        percentage = normalize_financial_unit(45, "%", field="revenue", market="H")

        self.assertEqual(eps["scale"], 1.0)
        self.assertEqual(eps["normalized_unit"], "HKD/share")
        self.assertEqual(percentage["allowed_usage"], "blocked")


if __name__ == "__main__":
    unittest.main()

