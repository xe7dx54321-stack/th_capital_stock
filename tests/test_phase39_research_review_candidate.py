import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase39_research_review_candidate_decision import build_payload
from phase39_helpers import make_phase39_conn


class Phase39ResearchReviewCandidateTests(unittest.TestCase):
    def test_research_review_candidate_is_not_pending(self):
        payload = build_payload(make_phase39_conn(), "300308.SZ")
        decision = payload["research_review_decision"]
        self.assertEqual(decision["decision"], "research_review_candidate")
        self.assertFalse(decision["promotion_boundary"]["pending_allowed"])
        self.assertFalse(decision["promotion_boundary"]["paper_order_allowed"])
        self.assertIn("supplier share unconfirmed", decision["why_not_pending"])
        self.assertFalse(payload["safety"]["research_review_candidate_is_pending"])


if __name__ == "__main__":
    unittest.main()
