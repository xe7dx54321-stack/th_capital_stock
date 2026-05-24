import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase12_data_quality_before_after import _field_quality_summary


class Phase12DataQualityBeforeAfterTests(unittest.TestCase):
    def test_field_quality_summary_counts_source_evidence(self):
        summary = _field_quality_summary(
            {
                "revenue": {"source_evidence_id": "ev_rev", "allowed_usage": "promotion_evidence"},
                "gross_margin": {"source_evidence_id": "ev_gm", "allowed_usage": "supporting_evidence"},
                "capex": {"allowed_usage": "blocked"},
            }
        )

        self.assertEqual(summary["source_evidence_field_count"], 2)
        self.assertIn("revenue", summary["promotion_evidence_fields"])
        self.assertIn("gross_margin", summary["supporting_evidence_fields"])
        self.assertIn("capex", summary["blocked_fields"])


if __name__ == "__main__":
    unittest.main()

