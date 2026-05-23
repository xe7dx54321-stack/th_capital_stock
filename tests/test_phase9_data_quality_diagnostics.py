import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase9_data_quality_diagnostics import field_quality_from_snapshot, root_causes_from_field_quality


class Phase9DataQualityDiagnosticsTests(unittest.TestCase):
    def test_missing_field_reason_becomes_root_cause(self):
        snapshot = {
            "field_details": {
                "gross_profit": {"extracted_value": None, "missing_reason": "mapping_missing", "confidence": 0.0},
                "revenue": {"extracted_value": 100.0, "source_evidence_id": "ev-1", "confidence": 0.8},
            },
            "field_missing_reasons": {"gross_profit": "mapping_missing"},
        }
        field_quality = field_quality_from_snapshot(snapshot)
        causes = root_causes_from_field_quality(field_quality)
        codes = {item["code"] for item in causes}

        self.assertEqual(field_quality["gross_profit"]["missing_reason"], "mapping_missing")
        self.assertIn("FIELD_MAPPING_MISSING", codes)

    def test_extracted_field_without_evidence_is_traceability_issue(self):
        snapshot = {
            "field_details": {
                "revenue": {"extracted_value": 100.0, "confidence": 0.8},
            }
        }
        causes = root_causes_from_field_quality(field_quality_from_snapshot(snapshot))

        self.assertIn("MISSING_SOURCE_EVIDENCE_ID", {item["code"] for item in causes})


if __name__ == "__main__":
    unittest.main()
