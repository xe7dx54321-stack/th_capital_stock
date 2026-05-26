import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_supplier_exposure_model import get_supplier_exposure_profile, validate_supplier_exposure_profile


class Phase25SupplierExposureModelTests(unittest.TestCase):
    def test_300394_profile_is_scenario_only_and_not_confirmed_customer_exposure(self):
        profile = get_supplier_exposure_profile("300394.SZ")
        self.assertEqual(profile["company_name"], "天孚通信")
        self.assertEqual(profile["customer_exposure_status"], "not_directly_confirmed")
        self.assertEqual(profile["allowed_usage"], "scenario_analysis_only")
        self.assertTrue(profile["assumption_required"])
        self.assertIsNone(profile["supplier_share_assumption_range"]["base"])
        self.assertFalse(any(issue["severity"] == "error" for issue in validate_supplier_exposure_profile(profile)))

    def test_missing_profile_is_blocked(self):
        profile = get_supplier_exposure_profile("000000.SZ")
        self.assertEqual(profile["status"], "missing")
        self.assertEqual(profile["allowed_usage"], "blocked")


if __name__ == "__main__":
    unittest.main()
