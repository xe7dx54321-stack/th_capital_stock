import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_expectation_gap import build_expectation_gap
from test_phase25_end_demand_proxy import make_evidence_conn


class Phase25ExpectationGapTests(unittest.TestCase):
    def test_expectation_gap_has_uncertainty_penalty_and_no_pending(self):
        payload = build_expectation_gap(make_evidence_conn(), "300394.SZ")
        gap = payload["expectation_gap"]
        self.assertIn(gap["status"], {"potential_positive_gap", "neutral", "insufficient_data"})
        self.assertLess(gap["drivers"]["uncertainty_penalty"], 0)
        self.assertNotEqual(gap["confidence"], "high")
        self.assertFalse(gap["promotion_allowed"])
        self.assertFalse(gap["safety"]["official_consensus_available"])
        self.assertFalse(gap["safety"]["expectation_gap_auto_pending"])


if __name__ == "__main__":
    unittest.main()
