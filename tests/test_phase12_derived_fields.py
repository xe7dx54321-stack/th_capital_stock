import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_derived_fundamentals import derive_free_cash_flow, derive_gross_margin


class Phase12DerivedFieldsTests(unittest.TestCase):
    def test_gross_margin_inherits_input_evidence(self):
        derived = derive_gross_margin(
            {
                "gross_profit": {"extracted_value": 40.0, "confidence": 0.8, "source_evidence_id": "ev_gp", "currency": "CNY"},
                "revenue": {"extracted_value": 100.0, "confidence": 0.9, "source_evidence_id": "ev_rev", "currency": "CNY"},
            }
        )

        self.assertAlmostEqual(derived["extracted_value"], 0.4)
        self.assertEqual(derived["extraction_method"], "derived")
        self.assertEqual(set(derived["input_evidence_ids"]), {"ev_gp", "ev_rev"})
        self.assertLessEqual(derived["confidence"], 0.8)

    def test_free_cash_flow_derived_and_missing_inputs(self):
        derived = derive_free_cash_flow(
            {
                "operating_cash_flow": {"extracted_value": 100.0, "confidence": 0.8, "source_evidence_id": "ev_ocf"},
                "capex": {"extracted_value": 30.0, "confidence": 0.7, "source_evidence_id": "ev_capex"},
            }
        )
        missing = derive_free_cash_flow({"operating_cash_flow": {"extracted_value": 100.0}})

        self.assertEqual(derived["extracted_value"], 70.0)
        self.assertEqual(set(derived["input_evidence_ids"]), {"ev_ocf", "ev_capex"})
        self.assertEqual(missing["missing_reason"], "derived_field_missing_inputs")
        self.assertEqual(missing["missing_inputs"], ["capex"])


if __name__ == "__main__":
    unittest.main()

