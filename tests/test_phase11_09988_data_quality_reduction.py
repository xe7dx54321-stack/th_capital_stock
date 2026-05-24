import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from validate_phase11_peer_historical_repaired_candidate import data_quality_summary


class Phase1109988DataQualityReductionTests(unittest.TestCase):
    def test_shareholders_equity_missing_root_cause_is_reduced(self):
        before = {
            "overall_data_quality_status": "degraded",
            "root_causes": [{"code": "FIELD_NOT_FOUND", "affected_fields": ["shareholders_equity"]}],
            "field_quality": {"shareholders_equity": {"status": "missing", "missing_reason": "field_not_found"}},
        }
        after = {
            "overall_data_quality_status": "degraded",
            "root_causes": [{"code": "FUNDAMENTALS_FIELD_CONFIDENCE_LOW", "affected_fields": ["shareholders_equity"]}],
            "field_quality": {"shareholders_equity": {"status": "extracted", "missing_reason": None}},
        }

        summary = data_quality_summary(before, after)

        self.assertIn("FIELD_NOT_FOUND:shareholders_equity", summary["resolved_root_causes"])
        self.assertEqual(summary["field_changes"]["shareholders_equity"]["after"], "extracted")


if __name__ == "__main__":
    unittest.main()
