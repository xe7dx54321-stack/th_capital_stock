import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in [("08_scripts", "lib"), ("08_scripts", "verification")]:
    path = ROOT.joinpath(*rel)
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase14_thesis_aware_multi_ticker_live import missing_fields_from_phase6


class Phase18CoreBlockerGateIntegrationTests(unittest.TestCase):
    def test_recovered_field_removed_from_phase6_missing_fields(self):
        row = {"fundamentals_missing_fields": ["revenue", "gross_profit"]}
        fundamentals = {
            "missing_fields": [],
            "revenue": 100.0,
            "gross_profit": 30.0,
            "field_details": {
                "revenue": {"source_evidence_id": "ev_rev", "confidence": 0.82, "allowed_usage": "supporting_evidence"},
                "gross_profit": {"source_evidence_id": "ev_rev", "input_evidence_ids": ["ev_rev", "ev_cost"], "confidence": 0.74, "allowed_usage": "supporting_evidence"},
            },
        }
        self.assertEqual(missing_fields_from_phase6(row, fundamentals), [])

    def test_low_confidence_recovered_field_still_blocks(self):
        row = {"fundamentals_missing_fields": ["revenue"]}
        fundamentals = {
            "missing_fields": [],
            "revenue": 100.0,
            "field_details": {"revenue": {"source_evidence_id": "ev_rev", "confidence": 0.42, "allowed_usage": "context_only"}},
        }
        self.assertEqual(missing_fields_from_phase6(row, fundamentals), ["revenue"])


if __name__ == "__main__":
    unittest.main()
