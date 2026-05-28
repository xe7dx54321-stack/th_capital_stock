import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase45_helpers import make_phase45_conn
from build_phase45_final_bear_case_review import build_payload


class Phase45BearCaseReviewTests(unittest.TestCase):
    def test_partially_mitigated_bear_case_still_blocks_pending(self):
        body = build_payload(make_phase45_conn(), "300308.SZ")["final_bear_case_review"]
        self.assertEqual(body["bear_case_status"], "partially_mitigated_but_not_cleared")
        self.assertNotEqual(body["bear_case_status"], "cleared")
        self.assertEqual(body["impact_on_research_conclusion"], "does_not_block_watchlist_research")
        self.assertEqual(body["impact_on_pending"], "blocks_investment_pending")


if __name__ == "__main__":
    unittest.main()
