import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase153Config(unittest.TestCase):
    def test_config(self):
        from smr_phase153_config import load_phase153_config
        c = load_phase153_config()
        self.assertEqual(c["phase"], "phase153")
        self.assertTrue(c["research_only"])
        self.assertFalse(c["activation_allowed"])
        self.assertFalse(c["auto_add_to_watchlist_allowed"])
        self.assertFalse(c["safety"]["llm_api_enabled"])
        self.assertFalse(c["safety"]["broker_integration_allowed"])

class TestPhase153ReviewPackets(unittest.TestCase):
    def setUp(self):
        self.c = {"ticker": "MRVL", "name": "Marvell Technology", "market": "US", "discovery_source": "theme_based", "priority": "high"}

    def test_identity_review(self):
        from smr_phase153_identity_review import build_identity_review_packet
        r = build_identity_review_packet(self.c)
        self.assertEqual(r["identity_status"], "verified")

    def test_source_route_review(self):
        from smr_phase153_source_route_review import build_source_route_review_packet
        r = build_source_route_review_packet(self.c)
        self.assertTrue(r["source_route_ready"])
        self.assertTrue(r["route_ready_not_equal_to_data_loaded"])

    def test_financial_route_review(self):
        from smr_phase153_financial_route_review import build_financial_route_review_packet
        r = build_financial_route_review_packet(self.c)
        self.assertTrue(r["financial_route_ready"])
        self.assertTrue(r["route_ready_not_equal_to_financials_loaded"])

    def test_valuation_route_review(self):
        from smr_phase153_valuation_route_review import build_valuation_route_review_packet
        r = build_valuation_route_review_packet(self.c)
        self.assertTrue(r["valuation_route_ready"])
        self.assertTrue(r["valuation_label_is_derived_only"])

    def test_evidence_review(self):
        from smr_phase153_evidence_review import build_evidence_review_packet
        r = build_evidence_review_packet(self.c)
        self.assertEqual(r["evidence_status"], "structural_anchor_exists")

    def test_risk_review(self):
        from smr_phase153_risk_review import build_risk_review_packet
        r = build_risk_review_packet(self.c)
        self.assertIn("market_risk", r["known_risks"])

    def test_thesis_seed_review(self):
        from smr_phase153_thesis_seed_review import build_thesis_seed_review_packet
        r = build_thesis_seed_review_packet(self.c)
        self.assertEqual(r["thesis_status"], "unconfirmed")

    def test_owner_checklist(self):
        from smr_phase153_owner_checklist import build_owner_approval_checklist
        r = build_owner_approval_checklist(self.c)
        self.assertTrue(r["all_items_pending"])
        self.assertTrue(r["owner_approval_not_equal_to_trade_approval"])

    def test_judge_review(self):
        from smr_phase153_judge_review import build_judge_agent_review_packet
        rp = {"identity_review": {"identity_status": "verified"}, "source_route_review": {"source_route_ready": True},
              "financial_route_review": {"financial_route_ready": True}, "valuation_route_review": {"valuation_route_ready": True}}
        r = build_judge_agent_review_packet(self.c, rp)
        self.assertEqual(r["judge_decision"], "ready_for_owner_approval")
        self.assertTrue(r["judge_decision_not_equal_to_investment_approval"])

class TestPhase153Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase153_onboarding_review_pipeline import run
        r = run("dry-run")
        p = r["phase153_onboarding_review_pipeline"]
        self.assertEqual(p["candidates_reviewed"], 8)
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["research_only"])
        self.assertFalse(p["activation_allowed"])
        self.assertFalse(p["auto_add_to_watchlist_allowed"])
        self.assertTrue(p["judge_pass_not_investment_approval"])
        self.assertTrue(p["onboarding_review_not_watch_activation"])
        self.assertFalse(p["watch_core_updated"])
        self.assertFalse(p["candidate_auto_activated"])
        self.assertEqual(p["mock_used"], False)
        self.assertEqual(p["trade_recommendation_created"], 0)
        self.assertEqual(p["target_price_created"], 0)
        self.assertEqual(p["paper_order_created"], 0)

if __name__ == "__main__":
    unittest.main()
