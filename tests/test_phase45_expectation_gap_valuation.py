import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase45_helpers import make_phase45_conn
from build_phase45_expectation_gap_valuation_boundary import build_payload, render_markdown


class Phase45ExpectationGapValuationTests(unittest.TestCase):
    def test_valuation_boundary_is_conservative_without_target_price(self):
        payload = build_payload(make_phase45_conn(), "300308.SZ")
        body = payload["expectation_gap_valuation_boundary"]
        self.assertEqual(body["expectation_gap_confidence"], "medium_low")
        self.assertFalse(body["official_consensus_confirmed"])
        self.assertEqual(body["valuation_boundary"], "scenario_analysis_only")
        self.assertFalse(body["investment_pending_allowed"])
        self.assertNotIn("target price", render_markdown(payload).lower())


if __name__ == "__main__":
    unittest.main()
