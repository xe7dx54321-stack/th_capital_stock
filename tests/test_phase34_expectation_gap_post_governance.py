import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase34_helpers import make_phase34_conn
from validate_phase34_expectation_gap_post_governance import build_payload


class Phase34ExpectationGapPostGovernanceTests(unittest.TestCase):
    def test_expectation_gap_is_not_forced_to_high_confidence(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        self.assertEqual(payload["summary"]["confidence_upgraded"], 0)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertIn(payload["ticker_results"][0]["after"]["confidence"], {"low", "low_to_medium", "unknown", None})


if __name__ == "__main__":
    unittest.main()
