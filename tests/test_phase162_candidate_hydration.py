import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase162Config(unittest.TestCase):
    def test_config(self):
        from smr_phase162_config import load_phase162_config
        c = load_phase162_config()
        self.assertEqual(c["phase"], "phase162")
        self.assertTrue(c["research_only"])
        self.assertTrue(c["free_sources_only"])
        self.assertFalse(c["target_price_output_allowed"])
        self.assertFalse(c["activation_execution_allowed"])

class TestPhase162DomainRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase162_domain_registry import build_phase162_domain_registry
        r = build_phase162_domain_registry()
        self.assertEqual(len(r["phase162_domain_registry"]["domains"]), 4)

class TestPhase162Loaders(unittest.TestCase):
    def test_loaders(self):
        from smr_phase162_loaders import load_phase153_context, load_phase151_context, load_source_fallback_policy
        for fn in [load_phase153_context, load_phase151_context, load_source_fallback_policy]:
            r = fn()
            self.assertFalse(list(r.values())[0]["mock_used"])

class TestPhase162Universe(unittest.TestCase):
    def test_universe(self):
        from smr_phase162_universe import build_hydration_universe
        u = build_hydration_universe()
        p = u["phase162_hydration_universe"]
        self.assertEqual(p["candidate_hydration_targets"], 13)
        self.assertTrue(p["minimum_targets_met"])
        self.assertTrue(p["preferred_targets_met"])

class TestPhase162Identity(unittest.TestCase):
    def test_identity(self):
        from smr_phase162_universe import build_hydration_universe
        from smr_phase162_identity import resolve_candidate_identities
        targets = build_hydration_universe()["phase162_hydration_universe"]["targets"]
        r = resolve_candidate_identities(targets)
        self.assertEqual(r["phase162_identity_resolver"]["identities_resolved"], 13)
        self.assertEqual(r["phase162_identity_resolver"]["identities_unresolved"], 0)

class TestPhase162SourcePlanner(unittest.TestCase):
    def test_routes(self):
        from smr_phase162_universe import build_hydration_universe
        from smr_phase162_source_planner import plan_candidate_source_routes
        targets = build_hydration_universe()["phase162_hydration_universe"]["targets"]
        r = plan_candidate_source_routes(targets)
        p = r["phase162_source_route_planner"]
        self.assertEqual(p["targets_planned"], 13)
        self.assertTrue(p["all_routes_free"])
        self.assertTrue(p["all_routes_no_login"])

class TestPhase162Hydration(unittest.TestCase):
    def setUp(self):
        from smr_phase162_universe import build_hydration_universe
        self.targets = build_hydration_universe()["phase162_hydration_universe"]["targets"]

    def test_quote(self):
        from smr_phase162_hydration import hydrate_quote_data
        r = hydrate_quote_data(self.targets, "skip-network")
        self.assertEqual(r["phase162_quote_hydration"]["sources_identified"], 13)
        self.assertTrue(r["phase162_quote_hydration"]["free_sources_only"])

    def test_financial(self):
        from smr_phase162_hydration import hydrate_financial_data
        r = hydrate_financial_data(self.targets, "skip-network")
        self.assertEqual(r["phase162_financial_hydration"]["financial_available_count"], 13)

    def test_valuation(self):
        from smr_phase162_hydration import hydrate_valuation_data
        r = hydrate_valuation_data(self.targets, "skip-network")
        self.assertEqual(r["phase162_valuation_hydration"]["target_price_created"], 0)
        self.assertEqual(r["phase162_valuation_hydration"]["target_price_created"],0)

    def test_news(self):
        from smr_phase162_hydration import hydrate_news_events
        r = hydrate_news_events(self.targets, "skip-network")
        self.assertEqual(r["phase162_news_event_hydration"]["trade_signal_created"], 0)
        self.assertEqual(r["phase162_news_event_hydration"]["trade_signal_created"],0)

class TestPhase162Availability(unittest.TestCase):
    def setUp(self):
        from smr_phase162_universe import build_hydration_universe
        self.targets = build_hydration_universe()["phase162_hydration_universe"]["targets"]

    def test_filing(self):
        from smr_phase162_availability import check_filing_availability
        r = check_filing_availability(self.targets)
        self.assertEqual(r["phase162_filing_availability"]["targets_checked"], 13)

    def test_source_probe(self):
        from smr_phase162_availability import probe_source_availability
        r = probe_source_availability(self.targets)
        self.assertTrue(r["phase162_source_probe"]["all_free_sources_available"])

class TestPhase162Scoring(unittest.TestCase):
    def setUp(self):
        from smr_phase162_universe import build_hydration_universe
        self.targets = build_hydration_universe()["phase162_hydration_universe"]["targets"]

    def test_completeness(self):
        from smr_phase162_scoring import score_hard_data_completeness
        r = score_hard_data_completeness(self.targets)
        self.assertTrue(r["phase162_completeness_scorer"]["all_core_fields_present"])

    def test_readiness(self):
        from smr_phase162_scoring import score_evidence_readiness
        r = score_evidence_readiness(self.targets)
        self.assertEqual(r["phase162_evidence_readiness_scorer"]["targets_checked"], 13)
        self.assertTrue(r["phase162_evidence_readiness_scorer"]["readiness_not_investment_rating"])

class TestPhase162Classifier(unittest.TestCase):
    def test_classifier(self):
        from smr_phase162_universe import build_hydration_universe
        from smr_phase162_classifier import classify_hydration_status
        targets = build_hydration_universe()["phase162_hydration_universe"]["targets"]
        r = classify_hydration_status(targets)
        self.assertEqual(r["phase162_hydration_classifier"]["targets_checked"], 13)
        self.assertTrue(r["phase162_hydration_classifier"]["hydration_not_approval"])

class TestPhase162FeedQueue(unittest.TestCase):
    def setUp(self):
        from smr_phase162_universe import build_hydration_universe
        from smr_phase162_scoring import score_evidence_readiness
        self.targets = build_hydration_universe()["phase162_hydration_universe"]["targets"]
        self.readiness = score_evidence_readiness(self.targets)

    def test_owner_feed(self):
        from smr_phase162_owner_feed import update_owner_review_feed
        r = update_owner_review_feed(self.targets, self.readiness)
        self.assertEqual(r["phase162_owner_review_feed"]["items"], 13)
        self.assertTrue(r["phase162_owner_review_feed"]["no_buy_sell_hold_language"])

    def test_agent_queue(self):
        from smr_phase162_agent_queue import update_agent_task_queue
        r = update_agent_task_queue(self.targets)
        self.assertTrue(r["phase162_agent_task_queue"]["no_trade_orders"])

class TestPhase162Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase162_guard import build_hydration_guard
        g = build_hydration_guard()
        self.assertEqual(g["phase162_hydration_guard"]["status"], "pass")
        self.assertEqual(g["phase162_hydration_guard"]["violations"], 0)

    def test_quality(self):
        from smr_phase162_quality_gate import build_quality_gate
        self.assertEqual(build_quality_gate()["phase162_quality_gate"]["status"], "pass")

    def test_cc(self):
        from smr_phase162_cannot_conclude_guard import build_cannot_conclude_guard
        cc = build_cannot_conclude_guard()
        self.assertEqual(cc["phase162_cannot_conclude_guard"]["status"], "pass")
        self.assertIn("300394 CNINFO org_id missing", cc["phase162_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase162Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase162_candidate_hydration_pipeline import run
        r = run("dry-run")
        p = r["phase162_candidate_hydration_pipeline"]
        self.assertEqual(p["targets_total"], 13)
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["cannot_conclude_guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["hydration_not_approval"])
        self.assertTrue(p["valuation_not_target_price"])
        self.assertTrue(p["news_not_trade_signal"])
        self.assertFalse(p["watch_core_updated"])
        self.assertEqual(p["target_price_created"], 0)

    def test_execute(self):
        from run_phase162_candidate_hydration_pipeline import run
        r = run("execute")
        self.assertEqual(r["phase162_candidate_hydration_pipeline"]["guard"], "pass")

    def test_skip_network(self):
        from run_phase162_candidate_hydration_pipeline import run
        r = run("skip-network")
        self.assertTrue(r["phase162_candidate_hydration_pipeline"]["skip_network_compatible"])

if __name__ == "__main__":
    unittest.main()
