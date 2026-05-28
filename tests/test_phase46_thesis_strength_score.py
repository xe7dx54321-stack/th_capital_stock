import unittest

import phase46_helpers  # noqa: F401
from build_phase46_thesis_strength_score import build_payload


class Phase46ThesisStrengthScoreTests(unittest.TestCase):
    def test_score_is_research_tracking_only(self):
        body = build_payload("300308.SZ")["thesis_strength_tracking"]
        self.assertEqual(body["thesis_strength_score"], 62)
        self.assertEqual(body["thesis_strength_bucket"], "watchlist_positive_but_unconfirmed")
        self.assertEqual(body["allowed_interpretation"], "research_tracking_only")
        self.assertIn("buy_signal", body["forbidden_interpretation"])
        self.assertIn("paper_order", body["forbidden_interpretation"])
        self.assertEqual(body["pending_created"], 0)
        self.assertEqual(body["paper_order_created"], 0)


if __name__ == "__main__":
    unittest.main()
