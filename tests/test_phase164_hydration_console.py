import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase164Config(unittest.TestCase):
    def test_config(self):
        from smr_phase164_config import load_phase164_config
        c = load_phase164_config()
        self.assertEqual(c["phase"], "phase164")
        self.assertTrue(c["static_html_only"])
        self.assertFalse(c["activation_execution_allowed"])
        self.assertFalse(c["target_price_output_allowed"])

class TestPhase164Domain(unittest.TestCase):
    def test_registry(self):
        from smr_phase164_domain_registry import build_phase164_domain_registry
        r = build_phase164_domain_registry()
        self.assertEqual(len(r["phase164_domain_registry"]["domains"]), 3)

class TestPhase164Loaders(unittest.TestCase):
    def test_loaders(self):
        from smr_phase164_loaders import load_phase163_context, load_phase162_context, load_phase158_context, load_phase146_context
        for fn in [load_phase163_context, load_phase162_context, load_phase158_context, load_phase146_context]:
            r = fn()
            self.assertFalse(list(r.values())[0]["mock_used"])

class TestPhase164NetworkSemantics(unittest.TestCase):
    def test_dry_semantics(self):
        from smr_phase164_network_semantics import resolve_network_mode_semantics
        r = resolve_network_mode_semantics("dry-run")
        self.assertTrue(r["phase164_network_semantics"]["dry_run_semantics_clarified"])
    def test_skip_semantics(self):
        from smr_phase164_network_semantics import resolve_network_mode_semantics
        r = resolve_network_mode_semantics("skip-network")
        self.assertTrue(r["phase164_network_semantics"]["skip_network_semantics_clarified"])

class TestPhase164ConsoleData(unittest.TestCase):
    def setUp(self):
        from smr_phase164_console_data import build_console_data_model
        self.model = build_console_data_model()

    def test_data_model(self):
        m = self.model["phase164_console_data_model"]
        self.assertEqual(m["total_candidates"], 13)

    def test_summary_panel(self):
        from smr_phase164_console_data import build_summary_panel
        r = build_summary_panel(self.model)
        self.assertIn("hydration-summary-panel", r["phase164_summary_panel"]["panel_html"])

    def test_hydration_cards(self):
        from smr_phase164_console_data import build_hydration_cards
        r = build_hydration_cards(self.model)
        self.assertEqual(r["phase164_hydration_cards"]["cards_count"], 13)
        self.assertTrue(r["phase164_hydration_cards"]["no_trade_language"])

    def test_snapshot_detail(self):
        from smr_phase164_console_data import build_snapshot_detail_panel
        r = build_snapshot_detail_panel(self.model)
        self.assertTrue(r["phase164_snapshot_detail_panel"]["valuation_not_target_price"])
        self.assertTrue(r["phase164_snapshot_detail_panel"]["news_not_trade_signal"])

    def test_freshness_panel(self):
        from smr_phase164_console_data import build_freshness_completeness_panel
        r = build_freshness_completeness_panel(self.model)
        self.assertTrue(r["phase164_freshness_completeness_panel"]["completeness_not_rating"])

    def test_limitation_panel(self):
        from smr_phase164_console_data import build_limitation_panel
        r = build_limitation_panel()
        self.assertIn("300394", r["phase164_limitation_panel"]["panel_html"])

    def test_monitoring_panel(self):
        from smr_phase164_console_data import build_monitoring_signal_panel
        r = build_monitoring_signal_panel(self.model)
        self.assertTrue(r["phase164_monitoring_signal_panel"]["no_buy_sell_hold"])

    def test_owner_feed_panel(self):
        from smr_phase164_console_data import build_owner_feed_panel
        r = build_owner_feed_panel()
        self.assertTrue(r["phase164_owner_feed_panel"]["no_buy_sell_hold"])

    def test_agent_queue_panel(self):
        from smr_phase164_console_data import build_agent_queue_panel
        r = build_agent_queue_panel()
        self.assertTrue(r["phase164_agent_queue_panel"]["no_trade_orders"])

    def test_ui_safety(self):
        from smr_phase164_console_data import build_ui_safety_copy
        r = build_ui_safety_copy()
        self.assertEqual(r["phase164_ui_safety_copy"]["overall_status"], "pass")

class TestPhase164AgentBridge(unittest.TestCase):
    def test_bridge(self):
        from smr_phase164_agent_bridge import build_agent_loop_bridge
        r = build_agent_loop_bridge()
        self.assertEqual(r["phase164_agent_loop_bridge"]["total_tasks"], 13)
        self.assertFalse(r["phase164_agent_loop_bridge"]["llm_api_called"])

    def test_scheduling(self):
        from smr_phase164_agent_bridge import build_scheduling_preview
        r = build_scheduling_preview()
        self.assertFalse(r["phase164_scheduling_preview"]["scheduler_registered"])
        self.assertTrue(r["phase164_scheduling_preview"]["preview_not_execution"])

class TestPhase164Activation(unittest.TestCase):
    def test_precheck(self):
        from smr_phase164_activation_precheck import build_activation_precheck
        r = build_activation_precheck()
        self.assertEqual(r["phase164_activation_precheck"]["total"], 13)
        self.assertEqual(r["phase164_activation_precheck"]["ready"], 0)
        self.assertTrue(r["phase164_activation_precheck"]["precheck_not_execution"])

class TestPhase164Console(unittest.TestCase):
    def test_page(self):
        from smr_phase164_console_page import build_console_page_html
        r = build_console_page_html()
        self.assertTrue(r["phase164_console_page"]["page_generated"])
        self.assertTrue(r["phase164_console_page"]["static_html"])
        self.assertFalse(r["phase164_console_page"]["external_js"])

    def test_nav(self):
        from smr_phase164_console_page import build_nav_integration
        r = build_nav_integration()
        self.assertTrue(r["phase164_nav_integration"]["integrated"])

    def test_css(self):
        from smr_phase164_console_page import build_css_extension
        r = build_css_extension()
        self.assertTrue(len(r["phase164_css_extension"]["css"]) > 100)

class TestPhase164Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase164_guard import build_console_guard
        g = build_console_guard()
        self.assertEqual(g["phase164_console_guard"]["status"], "pass")
    def test_quality(self):
        from smr_phase164_quality_gate import build_quality_gate
        self.assertEqual(build_quality_gate()["phase164_quality_gate"]["status"], "pass")
    def test_cc(self):
        from smr_phase164_cannot_conclude_guard import build_cannot_conclude_guard
        cc = build_cannot_conclude_guard()
        self.assertEqual(cc["phase164_cannot_conclude_guard"]["status"], "pass")

class TestPhase164Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase164_hydration_console_pipeline import run
        r = run("dry-run")
        p = r["phase164_hydration_console_pipeline"]
        self.assertEqual(p["cards"], 13)
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["console_not_approval"])
    def test_execute(self):
        from run_phase164_hydration_console_pipeline import run
        self.assertEqual(run("execute")["phase164_hydration_console_pipeline"]["guard"], "pass")
    def test_skip_network(self):
        from run_phase164_hydration_console_pipeline import run
        self.assertEqual(run("skip-network")["phase164_hydration_console_pipeline"]["guard"], "pass")

if __name__ == "__main__":
    unittest.main()
