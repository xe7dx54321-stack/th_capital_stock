import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase163Config(unittest.TestCase):
    def test_config(self):
        from smr_phase163_config import load_phase163_config
        c = load_phase163_config()
        self.assertEqual(c["phase"], "phase163")
        self.assertTrue(c["research_only"])
        self.assertFalse(c["raw_save_allowed"])
        self.assertFalse(c["activation_execution_allowed"])
        self.assertFalse(c["target_price_output_allowed"])

class TestPhase163Domain(unittest.TestCase):
    def test_registry(self):
        from smr_phase163_domain_registry import build_phase163_domain_registry
        r = build_phase163_domain_registry()
        self.assertEqual(len(r["phase163_domain_registry"]["domains"]), 3)

class TestPhase163TargetPlanner(unittest.TestCase):
    def test_planner(self):
        from smr_phase163_target_planner import plan_live_execute_targets
        r = plan_live_execute_targets()
        p = r["phase163_target_planner"]
        self.assertEqual(p["live_execute_targets"], 13)
        self.assertTrue(p["minimum_targets_met"])
        self.assertTrue(p["preferred_targets_met"])

class TestPhase163NetworkPolicy(unittest.TestCase):
    def test_policy(self):
        from smr_phase163_network_policy import build_network_mode_policy
        r = build_network_mode_policy("skip-network")
        p = r["phase163_network_policy"]
        self.assertEqual(p["mode"], "skip-network")
        self.assertFalse(p["execute_network_allowed"])
        self.assertTrue(p["free_sources_only"])

class TestPhase163Snapshots(unittest.TestCase):
    def setUp(self):
        from smr_phase163_target_planner import plan_live_execute_targets
        self.targets = plan_live_execute_targets()["phase163_target_planner"]["targets"]

    def test_quote_snapshot(self):
        from smr_phase163_snapshot import execute_quote_snapshot
        r = execute_quote_snapshot(self.targets, "skip-network")
        self.assertEqual(r["phase163_quote_snapshot"]["targets"], 13)
        self.assertEqual(r["phase163_quote_snapshot"]["snapshots_taken"], 0)

    def test_financial_snapshot(self):
        from smr_phase163_snapshot import execute_financial_snapshot
        r = execute_financial_snapshot(self.targets, "skip-network")
        self.assertEqual(r["phase163_financial_snapshot"]["snapshots_taken"], 0)

    def test_valuation_no_target_price(self):
        from smr_phase163_snapshot import execute_valuation_snapshot
        r = execute_valuation_snapshot(self.targets, "skip-network")
        self.assertEqual(r["phase163_valuation_snapshot"]["target_price_created"], 0)

    def test_news_no_trade_signal(self):
        from smr_phase163_snapshot import execute_news_snapshot
        r = execute_news_snapshot(self.targets, "skip-network")
        self.assertEqual(r["phase163_news_snapshot"]["trade_signal_created"], 0)

    def test_normalizer(self):
        from smr_phase163_snapshot import (execute_quote_snapshot, execute_financial_snapshot, execute_valuation_snapshot, execute_news_snapshot, normalize_snapshots)
        q = execute_quote_snapshot(self.targets, "skip-network")
        f = execute_financial_snapshot(self.targets, "skip-network")
        v = execute_valuation_snapshot(self.targets, "skip-network")
        n = execute_news_snapshot(self.targets, "skip-network")
        r = normalize_snapshots(q, f, v, n)
        self.assertEqual(r["phase163_snapshot_normalizer"]["total"], 13)
        self.assertFalse(r["phase163_snapshot_normalizer"]["raw_saved"])

    def test_freshness(self):
        from smr_phase163_snapshot import (execute_quote_snapshot, execute_financial_snapshot, execute_valuation_snapshot, execute_news_snapshot, normalize_snapshots, validate_freshness)
        targets = self.targets
        q = execute_quote_snapshot(targets, "skip-network")
        f = execute_financial_snapshot(targets, "skip-network")
        v = execute_valuation_snapshot(targets, "skip-network")
        n = execute_news_snapshot(targets, "skip-network")
        norm = normalize_snapshots(q, f, v, n)
        r = validate_freshness(norm)
        self.assertTrue(r["phase163_freshness_validator"]["needs_network_refresh"])

    def test_completeness(self):
        from smr_phase163_snapshot import (execute_quote_snapshot, execute_financial_snapshot, execute_valuation_snapshot, execute_news_snapshot, normalize_snapshots, score_completeness)
        targets = self.targets
        q = execute_quote_snapshot(targets, "skip-network")
        f = execute_financial_snapshot(targets, "skip-network")
        v = execute_valuation_snapshot(targets, "skip-network")
        n = execute_news_snapshot(targets, "skip-network")
        norm = normalize_snapshots(q, f, v, n)
        r = score_completeness(norm)
        self.assertTrue(r["phase163_completeness_scorer"]["completeness_not_rating"])

class TestPhase163LiveHydration(unittest.TestCase):
    def setUp(self):
        from smr_phase163_target_planner import plan_live_execute_targets
        from smr_phase163_snapshot import (execute_quote_snapshot, execute_financial_snapshot, execute_valuation_snapshot, execute_news_snapshot, normalize_snapshots)
        targets = plan_live_execute_targets()["phase163_target_planner"]["targets"]
        q = execute_quote_snapshot(targets, "skip-network")
        f = execute_financial_snapshot(targets, "skip-network")
        v = execute_valuation_snapshot(targets, "skip-network")
        n = execute_news_snapshot(targets, "skip-network")
        self.snapshots = normalize_snapshots(q, f, v, n)
        self.targets = targets

    def test_delta(self):
        from smr_phase163_live_hydration import compare_live_delta
        r = compare_live_delta(self.snapshots, "skip-network")
        self.assertTrue(r["phase163_delta_comparator"]["first_baseline"])
        self.assertTrue(r["phase163_delta_comparator"]["delta_not_signal"])

    def test_limitations(self):
        from smr_phase163_live_hydration import build_live_limitation_register
        r = build_live_limitation_register(self.targets, "skip-network")
        self.assertEqual(r["phase163_limitation_register"]["total"], 13)

class TestPhase163Monitoring(unittest.TestCase):
    def setUp(self):
        from smr_phase163_target_planner import plan_live_execute_targets
        self.targets = plan_live_execute_targets()["phase163_target_planner"]["targets"]

    def test_signals(self):
        from smr_phase163_monitoring import build_monitoring_signals
        r = build_monitoring_signals(self.targets, "skip-network")
        self.assertEqual(r["phase163_monitoring_signals"]["total"], 13)
        self.assertTrue(r["phase163_monitoring_signals"]["no_buy_sell_hold"])

    def test_daily_adapter(self):
        from smr_phase163_monitoring import build_monitoring_signals, build_daily_monitoring_adapter
        signals = build_monitoring_signals(self.targets, "skip-network")
        r = build_daily_monitoring_adapter(signals, "skip-network")
        self.assertTrue(r["phase163_daily_monitoring_adapter"]["daily_monitoring_not_watch_update"])
        self.assertFalse(r["phase163_daily_monitoring_adapter"]["watch_core_updated"])

class TestPhase163Refresh(unittest.TestCase):
    def setUp(self):
        from smr_phase163_target_planner import plan_live_execute_targets
        self.targets = plan_live_execute_targets()["phase163_target_planner"]["targets"]

    def test_owner_feed(self):
        from smr_phase163_refresh import refresh_owner_feed
        r = refresh_owner_feed(self.targets, "skip-network")
        self.assertEqual(r["phase163_owner_feed_refresh"]["items"], 13)
        self.assertTrue(r["phase163_owner_feed_refresh"]["no_buy_sell_hold"])

    def test_agent_queue(self):
        from smr_phase163_refresh import refresh_agent_queue
        r = refresh_agent_queue(self.targets, "skip-network")
        self.assertTrue(r["phase163_agent_queue_refresh"]["no_trade_orders"])

class TestPhase163Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase163_guard import build_live_hydration_guard
        g = build_live_hydration_guard()
        self.assertEqual(g["phase163_live_hydration_guard"]["status"], "pass")
        self.assertEqual(g["phase163_live_hydration_guard"]["violations"], 0)

    def test_quality(self):
        from smr_phase163_quality_gate import build_quality_gate
        self.assertEqual(build_quality_gate()["phase163_quality_gate"]["status"], "pass")

    def test_cc(self):
        from smr_phase163_cannot_conclude_guard import build_cannot_conclude_guard
        cc = build_cannot_conclude_guard()
        self.assertEqual(cc["phase163_cannot_conclude_guard"]["status"], "pass")
        self.assertIn("300394 CNINFO org_id missing", cc["phase163_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase163Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase163_live_hydration_pipeline import run
        r = run("dry-run")
        p = r["phase163_live_hydration_pipeline"]
        self.assertEqual(p["targets_total"], 13)
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["cannot_conclude_guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["snapshot_not_approval"])
        self.assertFalse(p["watch_core_updated"])
        self.assertEqual(p["valuation_target_price"], 0)
        self.assertEqual(p["news_trade_signal"], 0)
        self.assertFalse(p["raw_saved"])

    def test_execute(self):
        from run_phase163_live_hydration_pipeline import run
        r = run("execute")
        self.assertEqual(r["phase163_live_hydration_pipeline"]["guard"], "pass")

    def test_skip_network(self):
        from run_phase163_live_hydration_pipeline import run
        r = run("skip-network")
        self.assertEqual(r["phase163_live_hydration_pipeline"]["snapshots_deferred"], 13)

if __name__ == "__main__":
    unittest.main()
