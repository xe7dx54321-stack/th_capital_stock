import unittest

from build_phase47_thesis_strength_update import build_payload


class Phase47ThesisStrengthUpdateTests(unittest.TestCase):
    def test_score_unchanged_when_thesis_unchanged(self):
        payload = build_payload("300308.SZ", thesis_delta="unchanged")
        update = payload["thesis_strength_update"]
        self.assertEqual(update["previous_score"], 62)
        self.assertEqual(update["current_score"], 62)
        self.assertEqual(update["score_delta"], 0)
        self.assertEqual(update["thesis_delta"], "unchanged")

    def test_score_increase_when_strengthened(self):
        payload = build_payload("300308.SZ", thesis_delta="strengthened")
        update = payload["thesis_strength_update"]
        self.assertGreater(update["current_score"], update["previous_score"])
        self.assertEqual(update["score_delta"], 5)

    def test_score_decrease_when_weakened(self):
        payload = build_payload("300308.SZ", thesis_delta="weakened")
        update = payload["thesis_strength_update"]
        self.assertLess(update["current_score"], update["previous_score"])
        self.assertEqual(update["score_delta"], -5)

    def test_bucket_remains_watchlist_positive_at_62(self):
        payload = build_payload("300308.SZ")
        update = payload["thesis_strength_update"]
        self.assertEqual(update["current_bucket"], "watchlist_positive_but_unconfirmed")

    def test_forbidden_interpretations_present(self):
        payload = build_payload("300308.SZ")
        update = payload["thesis_strength_update"]
        self.assertIn("buy_signal", update["forbidden_interpretation"])
        self.assertIn("pending_approval", update["forbidden_interpretation"])
        self.assertIn("paper_order", update["forbidden_interpretation"])

    def test_allowed_interpretation_is_research_tracking(self):
        payload = build_payload("300308.SZ")
        update = payload["thesis_strength_update"]
        self.assertEqual(update["allowed_interpretation"], "research_tracking_only")

    def test_safety_gates(self):
        payload = build_payload("300308.SZ")
        safety = payload["safety"]
        self.assertFalse(safety["score_delta_is_buy_signal"])
        self.assertFalse(safety["score_delta_triggers_pending"])
        self.assertEqual(safety["pending_created"], 0)
        self.assertEqual(safety["paper_order_created"], 0)

    def test_markdown_output(self):
        from build_phase47_thesis_strength_update import render_markdown
        payload = build_payload("300308.SZ")
        md = render_markdown(payload)
        self.assertIn("Thesis Strength Update", md)
        self.assertIn("300308.SZ", md)


if __name__ == "__main__":
    unittest.main()
