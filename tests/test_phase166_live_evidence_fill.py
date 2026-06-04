import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase166Config(unittest.TestCase):
    def test_config(self):
        from smr_phase166_config import load_phase166_config
        c = load_phase166_config()
        self.assertEqual(c["phase"], "phase166")
        self.assertTrue(c["research_only"])
        self.assertTrue(c["live_evidence_fill_enabled"])
        self.assertTrue(c["agent_research_pass_rerun_enabled"])
        self.assertTrue(c["evidence_provenance_tracking_enabled"])
        self.assertTrue(c["agent_simulation_only"])
        self.assertFalse(c["llm_api_enabled"])
        self.assertFalse(c["live_llm_call_allowed"])
        self.assertFalse(c["activation_execution_allowed"])
        self.assertFalse(c["target_price_output_allowed"])
        self.assertFalse(c["position_sizing_allowed"])
        self.assertFalse(c["broker_integration_allowed"])

class TestPhase166Domain(unittest.TestCase):
    def test_registry(self):
        from smr_phase166_domain_registry import build_phase166_domain_registry
        r = build_phase166_domain_registry()
        self.assertEqual(len(r["phase166_domain_registry"]["domains"]), 3)
        self.assertEqual(len(r["phase166_domain_registry"]["candidates"]), 13)
        self.assertEqual(len(r["phase166_domain_registry"]["evidence_types"]), 6)

class TestPhase166Loaders(unittest.TestCase):
    def test_load_phase165_context(self):
        from smr_phase166_loaders import load_phase165_context
        r = load_phase165_context()
        self.assertEqual(r["phase165_context"]["research_packets"], 13)

    def test_load_phase164_context(self):
        from smr_phase166_loaders import load_phase164_context
        r = load_phase164_context()
        self.assertTrue(r["phase164_context"]["console_page"])

    def test_load_source_fallback(self):
        from smr_phase166_loaders import load_source_fallback_policy
        r = load_source_fallback_policy()
        self.assertTrue(r["phase166_source_fallback_policy"]["source_fallback_not_source_failure"])

class TestPhase166TargetPlanner(unittest.TestCase):
    def test_targets(self):
        from smr_phase166_target_planner import build_evidence_fill_targets
        r = build_evidence_fill_targets()
        t = r["phase166_evidence_fill_targets"]
        self.assertEqual(t["total_targets"], 78)
        self.assertTrue(t["minimum_targets_met"])
        self.assertTrue(t["preferred_targets_met"])

class TestPhase166NetworkGuard(unittest.TestCase):
    def test_dry_run_does_not_fetch(self):
        from smr_phase166_network_guard import build_network_mode_semantics_guard
        r = build_network_mode_semantics_guard("dry-run")
        g = r["phase166_network_mode_semantics_guard"]
        self.assertTrue(g["dry_run_does_not_fetch"])
        self.assertTrue(g["planned_evidence_is_not_live_evidence"])

    def test_execute_fetches(self):
        from smr_phase166_network_guard import build_network_mode_semantics_guard
        r = build_network_mode_semantics_guard("execute")
        self.assertTrue(r["phase166_network_mode_semantics_guard"]["evidence_actually_filled"])

    def test_skip_network_cached(self):
        from smr_phase166_network_guard import build_network_mode_semantics_guard
        r = build_network_mode_semantics_guard("skip-network")
        self.assertEqual(r["phase166_network_mode_semantics_guard"]["current_network_status"], "cached_only")

class TestPhase166SourcePlanner(unittest.TestCase):
    def test_source_planner(self):
        from smr_phase166_source_planner import build_live_evidence_source_planner
        r = build_live_evidence_source_planner()
        self.assertEqual(r["phase166_live_evidence_source_planner"]["total"], 13)
        self.assertTrue(r["phase166_live_evidence_source_planner"]["no_bypass_login_or_captcha"])

class TestPhase166EvidenceExecutors(unittest.TestCase):
    def test_quote_dry(self):
        from smr_phase166_evidence_executors import run_quote_evidence_fill
        r = run_quote_evidence_fill("dry-run")
        self.assertEqual(r["phase166_quote_evidence_fill"]["quotes_filled"], 0)
        self.assertEqual(r["phase166_quote_evidence_fill"]["quotes_planned"], 13)
        self.assertTrue(r["phase166_quote_evidence_fill"]["no_target_price_output"])

    def test_quote_execute(self):
        from smr_phase166_evidence_executors import run_quote_evidence_fill
        r = run_quote_evidence_fill("execute")
        self.assertEqual(r["phase166_quote_evidence_fill"]["quotes_filled"], 13)

    def test_financial_execute(self):
        from smr_phase166_evidence_executors import run_financial_evidence_fill
        r = run_financial_evidence_fill("execute")
        self.assertEqual(r["phase166_financial_evidence_fill"]["financials_filled"], 13)

    def test_valuation_no_target_price(self):
        from smr_phase166_evidence_executors import run_valuation_evidence_fill
        r = run_valuation_evidence_fill("execute")
        self.assertTrue(r["phase166_valuation_evidence_fill"]["no_target_price_output"])
        self.assertTrue(r["phase166_valuation_evidence_fill"]["derived_label_only"])

    def test_news_not_trade_signal(self):
        from smr_phase166_evidence_executors import run_news_event_evidence_fill
        r = run_news_event_evidence_fill("execute")
        self.assertTrue(r["phase166_news_event_evidence_fill"]["news_not_trade_signal"])

    def test_filing_availability(self):
        from smr_phase166_evidence_executors import run_filing_evidence_availability
        r = run_filing_evidence_availability("execute")
        self.assertEqual(r["phase166_filing_evidence_availability"]["filings_checked"], 13)

    def test_transcript_availability(self):
        from smr_phase166_evidence_executors import run_transcript_guidance_evidence_availability
        r = run_transcript_guidance_evidence_availability("execute")
        self.assertEqual(r["phase166_transcript_guidance_evidence_availability"]["transcripts_checked"], 13)

class TestPhase166Normalizer(unittest.TestCase):
    def test_normalizer(self):
        from smr_phase166_evidence_executors import (run_quote_evidence_fill, run_financial_evidence_fill, run_valuation_evidence_fill, run_news_event_evidence_fill, run_filing_evidence_availability, run_transcript_guidance_evidence_availability)
        from smr_phase166_normalizer import build_live_evidence_normalizer
        q = run_quote_evidence_fill("execute")
        f = run_financial_evidence_fill("execute")
        v = run_valuation_evidence_fill("execute")
        n = run_news_event_evidence_fill("execute")
        fl = run_filing_evidence_availability("execute")
        tr = run_transcript_guidance_evidence_availability("execute")
        r = build_live_evidence_normalizer(q, f, v, n, fl, tr)
        self.assertEqual(r["phase166_live_evidence_normalizer"]["candidates"], 13)
        self.assertTrue(r["phase166_live_evidence_normalizer"]["raw_payload_not_saved"])

class TestPhase166Provenance(unittest.TestCase):
    def test_provenance(self):
        from smr_phase166_provenance import build_evidence_provenance_tracker
        r = build_evidence_provenance_tracker("execute")
        self.assertEqual(r["phase166_evidence_provenance_tracker"]["candidates"], 13)
        self.assertEqual(r["phase166_evidence_provenance_tracker"]["provenance_entries"], 78)

class TestPhase166Validator(unittest.TestCase):
    def test_validator(self):
        from smr_phase166_evidence_executors import (run_quote_evidence_fill, run_financial_evidence_fill, run_valuation_evidence_fill, run_news_event_evidence_fill, run_filing_evidence_availability, run_transcript_guidance_evidence_availability)
        from smr_phase166_normalizer import build_live_evidence_normalizer
        from smr_phase166_validator import build_evidence_freshness_completeness_validator
        q = run_quote_evidence_fill("execute")
        f = run_financial_evidence_fill("execute")
        v = run_valuation_evidence_fill("execute")
        n = run_news_event_evidence_fill("execute")
        fl = run_filing_evidence_availability("execute")
        tr = run_transcript_guidance_evidence_availability("execute")
        norm = build_live_evidence_normalizer(q, f, v, n, fl, tr)
        r = build_evidence_freshness_completeness_validator(norm, "execute")
        val = r["phase166_evidence_freshness_completeness_validator"]
        self.assertEqual(val["candidates"], 13)
        self.assertTrue(val["freshness_not_trade_signal"])
        self.assertTrue(val["completeness_not_investment_rating"])

class TestPhase166Delta(unittest.TestCase):
    def test_delta(self):
        from smr_phase166_delta import build_evidence_gap_delta
        from smr_phase166_validator import build_evidence_freshness_completeness_validator
        v = build_evidence_freshness_completeness_validator({"phase166_live_evidence_normalizer":{"results":[{"ticker":"MRVL","quote_normalized":True,"financial_normalized":True,"valuation_normalized":True,"news_normalized":True,"filing_normalized":True,"transcript_normalized":True}]}}, "execute")
        r = build_evidence_gap_delta(v, "execute")
        self.assertEqual(r["phase166_evidence_gap_delta"]["candidates"], 1)
        self.assertTrue(r["phase166_evidence_gap_delta"]["delta_not_investment_rating"])

    def test_source_limits(self):
        from smr_phase166_delta import build_source_limitation_update
        r = build_source_limitation_update("execute")
        self.assertEqual(r["phase166_source_limitation_update"]["candidates"], 13)
        self.assertTrue(r["phase166_source_limitation_update"]["no_source_permanently_blocked"])

class TestPhase166AgentRerun(unittest.TestCase):
    def test_opportunity_rerun(self):
        from smr_phase166_agent_rerun import rerun_opportunity_agent
        r = rerun_opportunity_agent(True)
        o = r["phase166_opportunity_agent_rerun"]
        self.assertEqual(o["passes"], 13)
        self.assertTrue(o["agent_simulation_only"])
        self.assertFalse(o["llm_api_called"])
        self.assertTrue(o["rerun_not_auto_approval"])

    def test_evidence_rerun(self):
        from smr_phase166_agent_rerun import rerun_evidence_agent
        r = rerun_evidence_agent(True)
        self.assertEqual(r["phase166_evidence_agent_rerun"]["passes"], 13)

    def test_risk_rerun(self):
        from smr_phase166_agent_rerun import rerun_risk_agent
        r = rerun_risk_agent(True)
        self.assertEqual(r["phase166_risk_agent_rerun"]["passes"], 13)

    def test_thesis_rerun(self):
        from smr_phase166_agent_rerun import rerun_thesis_agent
        r = rerun_thesis_agent(True)
        self.assertEqual(r["phase166_thesis_agent_rerun"]["passes"], 13)

    def test_deepdive_rerun(self):
        from smr_phase166_agent_rerun import rerun_deepdive_agent
        r = rerun_deepdive_agent(True)
        self.assertEqual(r["phase166_deepdive_agent_rerun"]["passes"], 13)

    def test_brief_rerun(self):
        from smr_phase166_agent_rerun import rerun_brief_agent
        r = rerun_brief_agent(True)
        self.assertEqual(r["phase166_brief_agent_rerun"]["passes"], 13)

    def test_judge_rerun(self):
        from smr_phase166_agent_rerun import rerun_judge_agent
        r = rerun_judge_agent(True)
        j = r["phase166_judge_agent_rerun"]
        self.assertEqual(j["passes"], 13)
        self.assertTrue(j["trade_language_blocked"])
        self.assertEqual(j["trade_terms_found"], 0)
        self.assertTrue(j["agent_simulation_only"])
        self.assertFalse(j["llm_api_called"])

    def test_handoff_map(self):
        from smr_phase166_agent_rerun import build_updated_handoff_map
        r = build_updated_handoff_map()
        self.assertEqual(len(r["phase166_updated_handoff_map"]["agents"]), 7)
        self.assertTrue(r["phase166_updated_handoff_map"]["research_only"])

class TestPhase166PacketUpdater(unittest.TestCase):
    def test_packet_updater(self):
        from smr_phase166_delta import build_evidence_gap_delta
        from smr_phase166_validator import build_evidence_freshness_completeness_validator
        from smr_phase166_packet_updater import build_candidate_research_packet_updater
        v = build_evidence_freshness_completeness_validator({"phase166_live_evidence_normalizer":{"results":[{"ticker":"MRVL","quote_normalized":True,"financial_normalized":True,"valuation_normalized":True,"news_normalized":True,"filing_normalized":True,"transcript_normalized":True}]}}, "execute")
        d = build_evidence_gap_delta(v, "execute")
        r = build_candidate_research_packet_updater(None, d, "execute")
        p = r["phase166_candidate_research_packet_updater"]
        self.assertEqual(p["candidates"], 13)
        self.assertTrue(p["research_packets_not_thesis"])
        self.assertTrue(p["research_packets_not_advice"])

    def test_activation_preview(self):
        from smr_phase166_packet_updater import build_updated_activation_preview
        r = build_updated_activation_preview("execute")
        p = r["phase166_updated_activation_preview"]
        self.assertEqual(p["candidates"], 13)
        self.assertTrue(p["activation_preview_not_execution"])
        self.assertTrue(p["no_auto_activation"])

    def test_owner_action(self):
        from smr_phase166_packet_updater import build_updated_owner_review_action
        r = build_updated_owner_review_action("execute")
        p = r["phase166_updated_owner_review_action"]
        self.assertEqual(p["candidates"], 13)
        self.assertTrue(p["no_buy_sell_hold"])
        self.assertTrue(p["owner_action_not_trade"])

class TestPhase166Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase166_network_guard import build_network_mode_semantics_guard
        from smr_phase166_provenance import build_evidence_provenance_tracker
        from smr_phase166_validator import build_evidence_freshness_completeness_validator
        from smr_phase166_guard import build_research_only_evidence_fill_guard
        ng = build_network_mode_semantics_guard("execute")
        pv = build_evidence_provenance_tracker("execute")
        vl = build_evidence_freshness_completeness_validator({"phase166_live_evidence_normalizer":{"results":[{"ticker":"MRVL","quote_normalized":True,"financial_normalized":True,"valuation_normalized":True,"news_normalized":True,"filing_normalized":True,"transcript_normalized":True}]}}, "execute")
        r = build_research_only_evidence_fill_guard(ng, pv, vl)
        self.assertEqual(r["phase166_research_only_evidence_fill_guard"]["status"], "pass")
        self.assertEqual(r["phase166_research_only_evidence_fill_guard"]["violations"], 0)

    def test_quality_gate(self):
        from smr_phase166_delta import build_evidence_gap_delta
        from smr_phase166_validator import build_evidence_freshness_completeness_validator
        from smr_phase166_packet_updater import build_candidate_research_packet_updater
        from smr_phase166_quality_gate import build_quality_gate
        v = build_evidence_freshness_completeness_validator({"phase166_live_evidence_normalizer":{"results":[{"ticker":"MRVL","quote_normalized":True,"financial_normalized":True,"valuation_normalized":True,"news_normalized":True,"filing_normalized":True,"transcript_normalized":True}]}}, "execute")
        d = build_evidence_gap_delta(v, "execute")
        p = build_candidate_research_packet_updater(None, d, "execute")
        r = build_quality_gate(p, d, {"agent_rerun_not_auto_approval": True})
        self.assertEqual(r["phase166_quality_gate"]["status"], "pass")

    def test_cannot_conclude(self):
        from smr_phase166_cannot_conclude_guard import build_cannot_conclude_guard
        r = build_cannot_conclude_guard({}, {})
        self.assertEqual(r["phase166_cannot_conclude_guard"]["status"], "pass")
        self.assertIn("300394 CNINFO org_id missing", r["phase166_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase166Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase166_live_evidence_fill_pipeline import run
        r = run("dry-run")
        p = r["phase166_live_evidence_fill_pipeline"]
        self.assertEqual(p["candidates"], 13)
        self.assertFalse(p["evidence_filled"])
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)

    def test_execute(self):
        from run_phase166_live_evidence_fill_pipeline import run
        r = run("execute")
        p = r["phase166_live_evidence_fill_pipeline"]
        self.assertTrue(p["evidence_filled"])
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["live_evidence_not_owner_approval"])
        self.assertTrue(p["owner_action_not_trade"])
        self.assertFalse(p["watch_core_updated"])

    def test_skip_network(self):
        from run_phase166_live_evidence_fill_pipeline import run
        r = run("skip-network")
        self.assertEqual(r["phase166_live_evidence_fill_pipeline"]["guard"], "pass")

class TestPhase166Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase166_live_evidence_fill_board import build
        r = build("execute")
        b = r["phase166_live_evidence_fill_board"]
        self.assertEqual(b["candidates"], 13)
        self.assertEqual(b["guard"], "pass")
        self.assertEqual(b["violations"], 0)

    def test_brief(self):
        from build_phase166_live_evidence_fill_brief import build_brief
        r = build_brief("execute")
        b = r["phase166_live_evidence_fill_brief"]
        self.assertIn("boss_summary", b)
        self.assertTrue(b["boss_summary"]["no_trade_action"])

    def test_dashboard(self):
        from build_phase166_live_evidence_fill_dashboard import build_dashboard
        r = build_dashboard("execute")
        s = r["phase166_live_evidence_fill_dashboard"]["summary"]
        self.assertEqual(s["candidates"], 13)
        self.assertEqual(s["guard"], "pass")

if __name__ == "__main__":
    unittest.main()
