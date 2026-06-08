import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase187Registry(unittest.TestCase):
    def test_registry(self):
        from smr_phase187_real_web_scout_pilot import build_pilot_registry
        r = build_pilot_registry()
        reg = r["phase187_pilot_registry"]
        self.assertEqual(reg["pilot_ticker_count"],2)
        self.assertIn("MRVL",reg["pilot_tickers"]); self.assertIn("AMD",reg["pilot_tickers"])
        self.assertTrue(reg["real_web_allowed"]); self.assertTrue(reg["no_full_raw"]); self.assertTrue(reg["no_clean_evidence"])

class TestPhase187Scope(unittest.TestCase):
    def test_scope(self):
        from smr_phase187_real_web_scout_pilot import build_pilot_scope_selector
        s = build_pilot_scope_selector()
        self.assertEqual(s["phase187_pilot_scope"]["ticker_count"],2)
        self.assertEqual(s["phase187_pilot_scope"]["prompt_count"],4)
        self.assertTrue(s["phase187_pilot_scope"]["scope_limited_to_pilot"])

class TestPhase187QueryPlan(unittest.TestCase):
    def test_query_plan(self):
        from smr_phase187_real_web_scout_pilot import build_pilot_query_plan
        q = build_pilot_query_plan()
        self.assertEqual(q["phase187_query_plan"]["query_count"],8)
        self.assertTrue(q["phase187_query_plan"]["all_queries_designed"])

class TestPhase187NetworkPolicy(unittest.TestCase):
    def test_policy(self):
        from smr_phase187_real_web_scout_pilot import build_safe_network_policy
        p = build_safe_network_policy()
        self.assertTrue(p["phase187_safe_network_policy"]["robots_respected"])
        self.assertTrue(p["phase187_safe_network_policy"]["full_raw_disallowed"])
        self.assertTrue(p["phase187_safe_network_policy"]["login_disallowed"])

class TestPhase187Fetch(unittest.TestCase):
    def test_fetch_status(self):
        from smr_phase187_real_web_scout_pilot import build_fetch_status_board
        f = build_fetch_status_board()
        self.assertEqual(f["phase187_fetch_status"]["fetch_attempts"],8)
        self.assertTrue(f["phase187_fetch_status"]["all_raw_full_text_false"])
        self.assertTrue(f["phase187_fetch_status"]["all_excerpts_within_limit"])

class TestPhase187SourceLeads(unittest.TestCase):
    def test_source_leads(self):
        from smr_phase187_real_web_scout_pilot import build_source_lead_observations
        l = build_source_lead_observations()
        self.assertGreater(l["phase187_source_leads"]["lead_count"],0)
        self.assertTrue(l["phase187_source_leads"]["all_leads_not_verified"])
        self.assertTrue(l["phase187_source_leads"]["all_leads_not_clean_evidence"])
        for lead in l["phase187_source_leads"]["source_leads"]:
            self.assertTrue(lead["lead_not_verified_evidence"]); self.assertTrue(lead["lead_not_clean_evidence"])
            self.assertTrue(lead["would_help_not_completed"]); self.assertFalse(lead["raw_full_text_saved"])

class TestPhase187CrossCheckMatch(unittest.TestCase):
    def test_match_preview(self):
        from smr_phase187_real_web_scout_pilot import build_cross_check_match_preview
        c = build_cross_check_match_preview()
        self.assertGreater(c["phase187_cross_check_match_preview"]["match_count"],0)
        self.assertTrue(c["phase187_cross_check_match_preview"]["all_matches_preview"])

class TestPhase187Eligibility(unittest.TestCase):
    def test_eligibility_preview(self):
        from smr_phase187_real_web_scout_pilot import build_real_web_eligibility_preview
        e = build_real_web_eligibility_preview()
        self.assertTrue(e["phase187_eligibility_preview"]["all_eligible_preview_only"])
        self.assertTrue(e["phase187_eligibility_preview"]["eligible_not_clean_evidence"])

class TestPhase187Manifest(unittest.TestCase):
    def test_outcome_manifest(self):
        from smr_phase187_real_web_scout_pilot import build_pilot_outcome_manifest
        m = build_pilot_outcome_manifest()
        self.assertTrue(m["phase187_pilot_outcome_manifest"]["manifest_generated"])
        self.assertTrue(m["phase187_pilot_outcome_manifest"]["source_leads_not_clean_evidence"])
        self.assertTrue(m["phase187_pilot_outcome_manifest"]["no_full_raw_saved"])

class TestPhase187Breakdowns(unittest.TestCase):
    def test_ticker_breakdown(self):
        from smr_phase187_real_web_scout_pilot import build_ticker_pilot_breakdown
        b = build_ticker_pilot_breakdown()
        self.assertTrue(b["phase187_ticker_breakdown"]["within_limit"])
    def test_source_category_breakdown(self):
        from smr_phase187_real_web_scout_pilot import build_source_category_breakdown
        s = build_source_category_breakdown()
        self.assertGreater(s["phase187_source_category_breakdown"]["categories_found"],0)

class TestPhase187Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase187_real_web_scout_pilot import build_phase187_guard
        g = build_phase187_guard()
        self.assertEqual(g["phase187_guard"]["status"],"pass")
        self.assertTrue(g["phase187_guard"]["full_raw_save_disabled"])
    def test_quality_gate(self):
        from smr_phase187_real_web_scout_pilot import build_phase187_quality_gate
        q = build_phase187_quality_gate()
        self.assertEqual(q["phase187_quality_gate"]["status"],"pass"); self.assertEqual(q["phase187_quality_gate"]["violations"],0)
    def test_cc_guard(self):
        from smr_phase187_real_web_scout_pilot import build_phase187_cannot_conclude_guard
        c = build_phase187_cannot_conclude_guard()
        self.assertEqual(c["phase187_cannot_conclude_guard"]["status"],"pass")

class TestPhase187Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase187_pilot_board import build_pilot_board
        b = build_pilot_board(); self.assertEqual(b["phase187_pilot_board"]["guard"],"pass")
    def test_brief(self):
        from build_phase187_pilot_board import build_pilot_brief
        br = build_pilot_brief(); self.assertTrue(br["phase187_pilot_brief"]["source_leads_not_verified"])
    def test_dashboard(self):
        from build_phase187_pilot_board import build_dashboard
        d = build_dashboard(); self.assertEqual(d["phase187_dashboard"]["summary"]["guard"],"pass")

class TestPhase187Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase187_real_web_scout_pilot import run_pipeline
        r = run_pipeline("dry-run")
        p = r["phase187_real_web_scout_pilot_pipeline"]
        self.assertEqual(p["mode"],"dry-run"); self.assertEqual(p["guard"],"pass")
        self.assertEqual(p["pilot_ticker_count"],2)
    def test_execute(self):
        from run_phase187_real_web_scout_pilot import run_pipeline
        r = run_pipeline("execute")
        p = r["phase187_real_web_scout_pilot_pipeline"]
        self.assertTrue(p["source_lead_not_verified_evidence"]); self.assertTrue(p["would_help_not_completed"])
        self.assertTrue(p["eligibility_preview_not_clean_evidence_eligible"])
    def test_skip_network(self):
        from run_phase187_real_web_scout_pilot import run_pipeline
        r = run_pipeline("skip-network")
        p = r["phase187_real_web_scout_pilot_pipeline"]
        self.assertEqual(p["mode"],"skip-network"); self.assertEqual(p["quality_gate"],"pass")

class TestPhase187Safety(unittest.TestCase):
    def test_no_llm_clean(self):
        from run_phase187_real_web_scout_pilot import run_pipeline
        for mode in ["dry-run","execute","skip-network"]:
            r = run_pipeline(mode); p = r["phase187_real_web_scout_pilot_pipeline"]
            self.assertFalse(p["llm_api_called"]); self.assertFalse(p["clean_evidence_written"])
            self.assertFalse(p["raw_full_text_saved"]); self.assertFalse(p["login_used"])
            self.assertFalse(p["browser_automation_used"])
    def test_no_trade(self):
        from run_phase187_real_web_scout_pilot import run_pipeline
        r = run_pipeline("execute")
        p = r["phase187_real_web_scout_pilot_pipeline"]
        self.assertEqual(p["trade_recommendation_created"],0); self.assertEqual(p["target_price_created"],0)
        self.assertEqual(p["position_sizing_created"],0); self.assertEqual(p["broker_api_called"],False)

if __name__=="__main__": unittest.main()
