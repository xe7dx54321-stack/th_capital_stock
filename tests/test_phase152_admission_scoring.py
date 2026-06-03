import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase152Config(unittest.TestCase):
    def test_config_loads(self):
        from smr_phase152_config import load_phase152_config
        c = load_phase152_config()
        self.assertEqual(c["phase"], "phase152")
        self.assertTrue(c["research_only"])
        self.assertFalse(c["auto_add_to_watchlist_allowed"])
        self.assertFalse(c["auto_promote_to_core_allowed"])
        self.assertFalse(c["safety"]["llm_api_enabled"])
        self.assertFalse(c["safety"]["broker_integration_allowed"])

class TestPhase152Scorers(unittest.TestCase):
    def setUp(self):
        self.c = {"ticker": "MRVL", "name": "Marvell Technology", "market": "US",
                  "discovery_source": "theme_based", "trigger": "AI networking/ASIC theme", "priority": "high"}

    def test_identity_scorer(self):
        from smr_phase152_identity_scorer import score_identity_confidence
        r = score_identity_confidence(self.c)
        self.assertGreater(r["score"], 3.0)

    def test_source_scorer(self):
        from smr_phase152_source_scorer import score_source_availability
        r = score_source_availability(self.c)
        self.assertGreater(r["score"], 3.0)
        self.assertEqual(r["primary_source"], "SEC_EDGAR")

    def test_financial_scorer(self):
        from smr_phase152_financial_scorer import score_financial_route_readiness
        r = score_financial_route_readiness(self.c)
        self.assertGreater(r["score"], 3.0)

    def test_valuation_scorer(self):
        from smr_phase152_valuation_scorer import score_valuation_route_readiness
        r = score_valuation_route_readiness(self.c)
        self.assertGreater(r["score"], 2.0)

    def test_theme_scorer(self):
        from smr_phase152_theme_scorer import score_theme_fit
        r = score_theme_fit(self.c)
        self.assertEqual(r["score"], 5.0)

    def test_evidence_scorer(self):
        from smr_phase152_evidence_scorer import score_evidence_readiness
        r = score_evidence_readiness(self.c)
        self.assertGreater(r["score"], 2.0)

    def test_catalyst_scorer(self):
        from smr_phase152_catalyst_scorer import score_catalyst_novelty
        r = score_catalyst_novelty(self.c)
        self.assertGreater(r["score"], 2.0)

    def test_risk_scorer(self):
        from smr_phase152_risk_scorer import score_risk_penalty
        r = score_risk_penalty(self.c)
        self.assertFalse(r["higher_is_better"])

    def test_capacity_scorer(self):
        from smr_phase152_capacity_scorer import score_capacity_fit
        r = score_capacity_fit(self.c)
        self.assertGreater(r["score"], 2.0)

    def test_owner_scorer(self):
        from smr_phase152_owner_scorer import score_owner_relevance
        r = score_owner_relevance(self.c)
        self.assertGreater(r["score"], 2.0)

    def test_effort_scorer(self):
        from smr_phase152_effort_scorer import score_activation_effort
        r = score_activation_effort(self.c)
        self.assertFalse(r["higher_is_better"])

class TestPhase152Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase152_admission_scoring_pipeline import run
        r = run("dry-run")
        p = r["phase152_admission_scoring_pipeline"]
        self.assertEqual(p["scored_candidates"], 8)
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["research_only"])
        self.assertFalse(p["auto_add_to_watchlist_allowed"])
        self.assertTrue(p["admission_score_not_investment_rating"])
        self.assertEqual(p["mock_used"], False)
        self.assertEqual(p["trade_recommendation_created"], 0)
        self.assertEqual(p["target_price_created"], 0)
        self.assertEqual(p["paper_order_created"], 0)

if __name__ == "__main__":
    unittest.main()
