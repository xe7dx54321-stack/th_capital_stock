import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase167Config(unittest.TestCase):
    def test_config(self):
        from smr_phase167_config import load_phase167_config
        c = load_phase167_config()
        self.assertEqual(c["phase"], "phase167")
        self.assertTrue(c["research_only"])
        self.assertTrue(c["owner_review_console_enabled"])
        self.assertFalse(c["owner_input_write_allowed"])
        self.assertFalse(c["real_owner_decision_submission_allowed"])
        self.assertFalse(c["phase159_auto_submit_allowed"])
        self.assertFalse(c["activation_execution_allowed"])
        self.assertFalse(c["target_price_output_allowed"])

class TestPhase167Domain(unittest.TestCase):
    def test_registry(self):
        from smr_phase167_domain_registry import build_phase167_domain_registry
        r = build_phase167_domain_registry()
        self.assertEqual(len(r["phase167_domain_registry"]["domains"]), 4)
        self.assertEqual(len(r["phase167_domain_registry"]["candidates"]), 13)

class TestPhase167Loaders(unittest.TestCase):
    def test_load_phase166(self):
        from smr_phase167_loaders import load_phase166_live_evidence
        r = load_phase166_live_evidence()
        self.assertEqual(r["phase166_live_evidence"]["total_filled"], 78)
    def test_load_phase165(self):
        from smr_phase167_loaders import load_phase165_research_packets
        r = load_phase165_research_packets()
        self.assertEqual(r["phase165_research_packets"]["research_packets"], 13)
    def test_load_phase159(self):
        from smr_phase167_loaders import load_phase159_decision_schema
        r = load_phase159_decision_schema()
        self.assertTrue(r["phase159_decision_schema"]["auto_submit_disabled"])

class TestPhase167Universe(unittest.TestCase):
    def test_universe(self):
        from smr_phase167_universe import build_owner_review_universe
        r = build_owner_review_universe()
        self.assertEqual(r["phase167_owner_review_universe"]["candidates"], 13)
        self.assertTrue(r["phase167_owner_review_universe"]["minimum_targets_met"])

class TestPhase167DataModel(unittest.TestCase):
    def test_data_model(self):
        from smr_phase167_data_model import build_candidate_review_packet_data_model
        r = build_candidate_review_packet_data_model()
        self.assertEqual(r["phase167_candidate_review_packet_data_model"]["packets_built"], 13)

class TestPhase167Comparison(unittest.TestCase):
    def test_comparison(self):
        from smr_phase167_comparison import build_candidate_comparison_matrix
        r = build_candidate_comparison_matrix()
        m = r["phase167_candidate_comparison_matrix"]
        self.assertEqual(m["candidates"], 13)
        self.assertTrue(m["comparison_matrix_not_investment_ranking"])
        self.assertTrue(m["no_buy_sell_hold_in_matrix"])

class TestPhase167Panels(unittest.TestCase):
    def test_evidence_provenance(self):
        from smr_phase167_panels import build_evidence_provenance_summary
        r = build_evidence_provenance_summary()
        self.assertEqual(r["phase167_evidence_provenance_summary"]["candidates"], 13)
    def test_agent_rerun(self):
        from smr_phase167_panels import build_agent_rerun_summary_panel
        r = build_agent_rerun_summary_panel()
        self.assertTrue(r["phase167_agent_rerun_summary_panel"]["all_7_agents_rerun_complete"])
    def test_readiness_delta(self):
        from smr_phase167_panels import build_readiness_delta_summary_panel
        r = build_readiness_delta_summary_panel()
        self.assertTrue(r["phase167_readiness_delta_summary_panel"]["readiness_delta_not_investment_rating"])

class TestPhase167ReviewCards(unittest.TestCase):
    def test_cards(self):
        from smr_phase167_review_cards import build_candidate_review_cards
        r = build_candidate_review_cards()
        self.assertEqual(r["phase167_candidate_review_cards"]["cards_generated"], 13)

class TestPhase167DecisionPrep(unittest.TestCase):
    def test_priority(self):
        from smr_phase167_decision_prep import build_owner_review_priority_classifier
        r = build_owner_review_priority_classifier()
        self.assertEqual(len(r["phase167_owner_review_priority_classifier"]["rows"]), 13)
        self.assertTrue(r["phase167_owner_review_priority_classifier"]["priority_not_investment_rating"])
    def test_taxonomy(self):
        from smr_phase167_decision_prep import build_activation_decision_prep_taxonomy
        r = build_activation_decision_prep_taxonomy()
        self.assertEqual(len(r["phase167_activation_decision_prep_taxonomy"]["options"]), 4)
        self.assertTrue(r["phase167_activation_decision_prep_taxonomy"]["no_buy_sell_hold"])
    def test_prep_package(self):
        from smr_phase167_decision_prep import build_candidate_decision_prep_package
        r = build_candidate_decision_prep_package()
        self.assertEqual(r["phase167_candidate_decision_prep_package"]["packages_generated"], 13)
        self.assertTrue(r["phase167_candidate_decision_prep_package"]["no_buy_sell_hold"])
    def test_input_draft(self):
        from smr_phase167_decision_prep import build_owner_decision_input_draft
        r = build_owner_decision_input_draft()
        self.assertTrue(r["phase167_owner_decision_input_draft"]["draft_not_written_to_real_input"])
        self.assertTrue(r["phase167_owner_decision_input_draft"]["draft_not_final_owner_decision"])
        self.assertFalse(r["phase167_owner_decision_input_draft"]["owner_input_write_allowed"])
    def test_safety_validator(self):
        from smr_phase167_decision_prep import build_owner_decision_input_draft, build_candidate_decision_prep_package, build_owner_decision_safety_validator
        d = build_owner_decision_input_draft()
        p = build_candidate_decision_prep_package()
        r = build_owner_decision_safety_validator(d, p)
        self.assertEqual(r["phase167_owner_decision_safety_validator"]["status"], "pass")

class TestPhase167Workbench(unittest.TestCase):
    def test_checklist(self):
        from smr_phase167_workbench import build_review_checklist
        r = build_review_checklist()
        self.assertTrue(r["phase167_review_checklist"]["checklist_not_trade_actions"])
    def test_gaps(self):
        from smr_phase167_workbench import build_remaining_evidence_gap_panel
        r = build_remaining_evidence_gap_panel()
        self.assertEqual(r["phase167_remaining_evidence_gap_panel"]["candidates"], 13)

class TestPhase167ActionQueues(unittest.TestCase):
    def test_owner_queue(self):
        from smr_phase167_action_queues import build_owner_action_queue_update
        r = build_owner_action_queue_update()
        self.assertTrue(r["phase167_owner_action_queue_update"]["no_buy_sell_hold"])
    def test_agent_queue(self):
        from smr_phase167_action_queues import build_agent_follow_up_queue_update
        r = build_agent_follow_up_queue_update()
        self.assertTrue(r["phase167_agent_follow_up_queue_update"]["no_trade_order_target"])

class TestPhase167Console(unittest.TestCase):
    def test_nav(self):
        from smr_phase167_console import build_console_navigation_integration
        r = build_console_navigation_integration()
        self.assertTrue(r["phase167_console_navigation_integration"]["static_html_only"])
    def test_css(self):
        from smr_phase167_console import build_static_css_extension
        r = build_static_css_extension()
        self.assertTrue(r["phase167_static_css_extension"]["static_html_only"])
    def test_page(self):
        from smr_phase167_console import build_owner_review_console_page
        r = build_owner_review_console_page()
        self.assertTrue(r["phase167_owner_review_console_page"]["page_generated"])
        self.assertFalse(r["phase167_owner_review_console_page"]["execution_button_enabled"])
        self.assertFalse(r["phase167_owner_review_console_page"]["trade_button_enabled"])
    def test_link(self):
        from smr_phase167_console import build_link_integrity_checker
        r = build_link_integrity_checker()
        self.assertEqual(r["phase167_link_integrity_checker"]["status"], "pass")
    def test_ui_safety(self):
        from smr_phase167_console import build_ui_copy_safety_checker
        r = build_ui_copy_safety_checker()
        self.assertEqual(r["phase167_ui_copy_safety_checker"]["status"], "pass")

class TestPhase167Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase167_decision_prep import build_owner_decision_input_draft, build_candidate_decision_prep_package
        from smr_phase167_guard import build_research_only_owner_review_guard
        d = build_owner_decision_input_draft()
        p = build_candidate_decision_prep_package()
        r = build_research_only_owner_review_guard(d, p)
        self.assertEqual(r["phase167_research_only_owner_review_guard"]["status"], "pass")
    def test_quality_gate(self):
        from smr_phase167_comparison import build_candidate_comparison_matrix
        from smr_phase167_decision_prep import build_candidate_decision_prep_package
        from smr_phase167_guard import build_quality_gate
        c = build_candidate_comparison_matrix()
        p = build_candidate_decision_prep_package()
        r = build_quality_gate(c, p)
        self.assertEqual(r["phase167_quality_gate"]["status"], "pass")
    def test_cc(self):
        from smr_phase167_guard import build_cannot_conclude_guard
        r = build_cannot_conclude_guard({}, {})
        self.assertEqual(r["phase167_cannot_conclude_guard"]["status"], "pass")
        self.assertIn("300394 CNINFO org_id missing", r["phase167_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase167Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase167_owner_review_board import build
        r = build()
        b = r["phase167_owner_review_board"]
        self.assertEqual(b["candidates"], 13)
        self.assertEqual(b["guard"], "pass")
        self.assertEqual(b["violations"], 0)
    def test_brief(self):
        from build_phase167_owner_review_brief import build_brief
        r = build_brief()
        self.assertTrue(r["phase167_owner_review_brief"]["boss_summary"]["no_trade_action"])
    def test_dashboard(self):
        from build_phase167_owner_review_dashboard import build_dashboard
        r = build_dashboard()
        s = r["phase167_owner_review_dashboard"]["summary"]
        self.assertEqual(s["guard"], "pass")

class TestPhase167Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase167_owner_review_pipeline import run
        r = run("dry-run")
        p = r["phase167_owner_review_pipeline"]
        self.assertEqual(p["candidates"], 13)
        self.assertEqual(p["guard"], "pass")
        self.assertTrue(p["comparison_matrix_not_investment_ranking"])
        self.assertTrue(p["draft_not_written_to_real_input"])
    def test_execute(self):
        from run_phase167_owner_review_pipeline import run
        r = run("execute")
        p = r["phase167_owner_review_pipeline"]
        self.assertEqual(p["guard"], "pass")
        self.assertFalse(p["watch_core_updated"])
    def test_skip(self):
        from run_phase167_owner_review_pipeline import run
        r = run("skip-network")
        self.assertEqual(r["phase167_owner_review_pipeline"]["guard"], "pass")

if __name__ == "__main__":
    unittest.main()
