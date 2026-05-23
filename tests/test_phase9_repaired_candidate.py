import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from validate_phase9_repaired_candidate import blocker_codes, field_state


class Phase9RepairedCandidateTests(unittest.TestCase):
    def test_before_after_helpers_are_specific(self):
        item = {"blocking_factors": [{"code": "VALUATION_NOT_PROMOTION_ELIGIBLE"}, {"code": "HIGH_BEAR_CASE"}]}
        snapshot = {
            "field_details": {
                "gross_profit": {"extracted_value": 1.0, "missing_reason": None},
                "eps_basic": {"extracted_value": None, "missing_reason": "field_not_found"},
                "capex": {"extracted_value": None, "missing_reason": "table_not_found"},
                "free_cash_flow": {"extracted_value": None, "missing_reason": "derived_field_missing_inputs"},
                "shareholders_equity": {"extracted_value": 10.0, "missing_reason": None},
            }
        }
        repaired, missing = field_state(snapshot)

        self.assertEqual(blocker_codes(item), ["VALUATION_NOT_PROMOTION_ELIGIBLE", "HIGH_BEAR_CASE"])
        self.assertIn("gross_profit", repaired)
        self.assertIn("shareholders_equity", repaired)
        self.assertIn("capex", missing)


if __name__ == "__main__":
    unittest.main()
