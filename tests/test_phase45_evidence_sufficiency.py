import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase45_helpers import make_phase45_conn
from build_phase45_final_evidence_sufficiency_review import build_payload


class Phase45EvidenceSufficiencyTests(unittest.TestCase):
    def test_research_and_investment_sufficiency_are_separate(self):
        body = build_payload(make_phase45_conn(), "300308.SZ")["evidence_sufficiency_review"]
        self.assertEqual(body["evidence_sufficiency_for_research_conclusion"], "sufficient_for_watchlist_research")
        self.assertEqual(body["evidence_sufficiency_for_investment_pending"], "insufficient")
        self.assertFalse(body["promotion_safety"]["pending_allowed"])
        self.assertEqual(body["manual_candidates"]["confirmed_variables_added"], 0)


if __name__ == "__main__":
    unittest.main()
