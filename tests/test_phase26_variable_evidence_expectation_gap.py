import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, VERIFICATION_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from test_phase26_capacity_shipment_evidence import make_capacity_conn
from validate_phase26_variable_evidence_expectation_gap import build_payload


class Phase26VariableEvidenceExpectationGapTests(unittest.TestCase):
    def test_variable_evidence_does_not_force_confidence_or_pending(self):
        payload = build_payload(make_capacity_conn(), tickers="300394.SZ")
        row = payload["ticker_results"][0]
        self.assertEqual(payload["summary"]["promotion_allowed_from_gap_only"], 0)
        self.assertIn("ASP missing", row["why_not_upgraded"])
        self.assertFalse(row["promotion_allowed_from_gap_only"])
        self.assertNotEqual(row["after"]["confidence"], "high")


if __name__ == "__main__":
    unittest.main()
