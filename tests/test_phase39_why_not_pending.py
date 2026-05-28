import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase39_why_not_pending_reinforcement import build_payload
from phase39_helpers import make_phase39_conn


class Phase39WhyNotPendingTests(unittest.TestCase):
    def test_reinforcement_keeps_pending_false(self):
        payload = build_payload(make_phase39_conn(), "300308.SZ")
        body = payload["why_not_pending_reinforcement"]
        self.assertTrue(body["research_review_candidate"])
        self.assertFalse(body["pending_allowed"])
        self.assertFalse(body["promotion_boundary"]["paper_order_allowed"])
        blockers = [item["blocker"] for item in body["main_blockers"]]
        self.assertIn("official_consensus_missing", blockers)
        self.assertIn("product_mix", body["what_improved_but_not_enough"])


if __name__ == "__main__":
    unittest.main()
