import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase34_helpers import make_phase34_conn
from validate_phase34_bear_case_post_governance import build_payload


class Phase34BearCasePostGovernanceTests(unittest.TestCase):
    def test_bear_case_delta_is_explained_and_not_promotion(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        row = payload["ticker_results"][0]
        self.assertIn(row["delta"], {"worsened", "unchanged"})
        self.assertTrue(row["remaining_bear_points"])
        self.assertFalse(payload["safety"]["bear_case_change_triggers_promotion"])


if __name__ == "__main__":
    unittest.main()
