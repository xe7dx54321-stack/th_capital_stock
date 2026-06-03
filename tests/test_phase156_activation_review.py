import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase156Config(unittest.TestCase):
    def test_config(self):
        from smr_phase156_config import load_phase156_config
        c = load_phase156_config()
        self.assertEqual(c["phase"], "phase156")
        self.assertTrue(c["research_only"])
        self.assertTrue(c["owner_manual_activation_review_enabled"])
        self.assertFalse(c["auto_owner_approval_allowed"])
        self.assertEqual(c["default_owner_decision"], "pending_owner_review")
        self.assertFalse(c["activation_allowed"])

class TestPhase156Decisions(unittest.TestCase):
    def setUp(self):
        self.candidates = [{"ticker":"MRVL","name":"Marvell","market":"US","composite_score":4.2},{"ticker":"INTC","name":"Intel","market":"US","composite_score":4.2}]
        self.templates = [{"ticker":"MRVL","owner_decision":"pending_owner_review","rationale":""},{"ticker":"INTC","owner_decision":"pending_owner_review","rationale":""}]

    def test_review_input_defaults_pending(self):
        from smr_phase156_activation_review_input import build_activation_review_input
        r = build_activation_review_input(self.candidates)
        self.assertEqual(r["phase156_activation_review_input"]["candidates_for_review"], 2)
        self.assertTrue(r["phase156_activation_review_input"]["all_default_to_pending"])

    def test_decision_intake_no_auto_approve(self):
        from smr_phase156_decision_intake import build_owner_decision_intake
        r = build_owner_decision_intake(self.candidates)
        self.assertTrue(r["phase156_decision_intake"]["no_auto_approval"])
        for t in r["phase156_decision_intake"]["templates"]:
            self.assertEqual(t["owner_decision"], "pending_owner_review")

    def test_classifier_all_pending(self):
        from smr_phase156_activation_review_input import build_activation_review_input
        from smr_phase156_decision_classifier import classify_owner_decisions
        inp = build_activation_review_input(self.candidates)
        r = classify_owner_decisions(inp["phase156_activation_review_input"])
        s = r["phase156_decision_classifier"]["summary"]
        self.assertEqual(s["pending_owner_review"], 2)
        self.assertEqual(s["approved"], 0)

    def test_watch_core_guard(self):
        from smr_phase156_watch_core_guard import run_watch_core_update_guard
        r = run_watch_core_update_guard()
        self.assertFalse(r["phase156_watch_core_guard"]["watch_core_updated"])
        self.assertFalse(r["phase156_watch_core_guard"]["candidate_auto_activated"])

    def test_tier_proposal_not_executed(self):
        from smr_phase156_tier_update_proposal import build_tier_update_proposal
        r = build_tier_update_proposal({})
        self.assertTrue(r["phase156_tier_update_proposal"]["proposal_is_not_executed"])

class TestPhase156Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase156_activation_review_pipeline import run
        r = run("dry-run")
        p = r["phase156_activation_review_pipeline"]
        self.assertEqual(p["candidates_for_review"], 8)
        self.assertEqual(p["pending_owner_review"], 8)
        self.assertEqual(p["approved"], 0)
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["owner_approval_not_trade_approval"])
        self.assertTrue(p["approve_not_equal_to_buy"])
        self.assertTrue(p["reject_not_equal_to_sell"])
        self.assertFalse(p["watch_core_updated"])
        self.assertEqual(p["mock_used"], False)

if __name__ == "__main__":
    unittest.main()
