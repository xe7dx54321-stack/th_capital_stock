import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_revenue_sensitivity_model import build_revenue_sensitivity


class Phase25RevenueSensitivityModelTests(unittest.TestCase):
    def test_revenue_sensitivity_does_not_force_missing_variables(self):
        payload = build_revenue_sensitivity(sqlite3.connect(":memory:"), "300394.SZ")
        sensitivity = payload["revenue_sensitivity"]
        self.assertEqual(sensitivity["status"], "scenario_analysis")
        self.assertEqual(sensitivity["allowed_usage"], "scenario_analysis_only")
        self.assertIn("supplier_share", sensitivity["missing_variables"])
        self.assertIn("ASP", sensitivity["missing_variables"])
        self.assertIsNone(sensitivity["scenario_cases"]["base"]["incremental_revenue_proxy"])
        self.assertFalse(sensitivity["safety"]["supplier_share_fabricated"])
        self.assertFalse(sensitivity["safety"]["ASP_fabricated"])


if __name__ == "__main__":
    unittest.main()
