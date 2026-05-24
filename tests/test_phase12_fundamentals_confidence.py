import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_fundamentals_confidence import score_fundamental_field


class Phase12FundamentalsConfidenceTests(unittest.TestCase):
    def test_confidence_breakdown_and_usage(self):
        scored = score_fundamental_field(
            "revenue",
            {
                "field": "revenue",
                "extracted_value": 100.0,
                "unit": "million CNY",
                "unit_confidence": 0.95,
                "source_evidence_id": "ev_revenue",
                "confidence": 0.85,
                "period": "FY2025",
                "chunk_section_type": "financial_statement",
                "missing_reason": None,
            },
            source_quality="primary",
        )

        self.assertIn("source_evidence", scored["confidence_breakdown"])
        self.assertEqual(scored["confidence_level"], "high")
        self.assertEqual(scored["allowed_usage"], "promotion_evidence")

    def test_low_confidence_field_cannot_be_promotion_evidence(self):
        scored = score_fundamental_field(
            "gross_profit",
            {
                "field": "gross_profit",
                "extracted_value": 100.0,
                "unit_confidence": 0.95,
                "confidence": 0.2,
                "missing_reason": None,
            },
            source_quality="secondary",
        )

        self.assertNotEqual(scored["allowed_usage"], "promotion_evidence")


if __name__ == "__main__":
    unittest.main()

