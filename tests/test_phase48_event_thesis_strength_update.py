import unittest
from build_phase48_event_thesis_strength_update import build_payload

class Phase48EventThesisStrengthUpdateTests(unittest.TestCase):
    def test_score_unchanged_or_strengthened(self):
        p = build_payload("300308.SZ")
        u = p["thesis_strength_update"]
        self.assertGreaterEqual(u["current_score"], 62)
        self.assertEqual(u["thesis_delta"], "unchanged_or_modestly_strengthened")
    def test_allowed_interpretation(self):
        p = build_payload("300308.SZ")
        u = p["thesis_strength_update"]
        self.assertEqual(u["allowed_interpretation"], "research_tracking_only")
    def test_forbidden_interpretation(self):
        p = build_payload("300308.SZ")
        u = p["thesis_strength_update"]
        self.assertIn("buy_signal", u["forbidden_interpretation"])
        self.assertIn("pending_approval", u["forbidden_interpretation"])
if __name__ == "__main__": unittest.main()
