import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase182ScoutUniverse(unittest.TestCase):
    def test_activated_candidates(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_activated_candidate_scout_universe
        u = build_activated_candidate_scout_universe()
        su = u["phase182_scout_universe"]
        self.assertEqual(su["activated_candidate_count"],9)
        self.assertEqual(len(su["rows"]),9)
        for r in su["rows"]:
            self.assertTrue(r["scout_enabled"])
            self.assertEqual(r["scout_status"],"prompt_pack_designed")
            self.assertTrue(r["llm_not_called"])
        self.assertFalse(su["mock_used"])

class TestPhase182PromptTaxonomy(unittest.TestCase):
    def test_taxonomy(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_scout_prompt_taxonomy
        t = build_scout_prompt_taxonomy()
        tx = t["phase182_prompt_taxonomy"]
        self.assertEqual(tx["prompt_type_count"],8)
        self.assertEqual(len(tx["prompt_types"]),8)
        expected = ["general_news_scout","management_commentary_scout","customer_demand_scout",
                    "supply_chain_crosscheck_scout","product_pricing_lead_time_scout",
                    "filing_official_source_scout","risk_negative_signal_scout","contradiction_scout"]
        for e in expected:
            self.assertIn(e,tx["prompt_types"])

class TestPhase182PromptCards(unittest.TestCase):
    def test_prompt_cards(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_scout_prompt_cards
        c = build_scout_prompt_cards()
        pc = c["phase182_prompt_cards"]
        self.assertEqual(pc["prompt_card_count"],8)
        self.assertEqual(pc["prompt_type_count"],8)
        self.assertTrue(pc["all_cards_research_only"])
        for card in pc["prompt_cards"]:
            self.assertIn("prompt_id",card)
            self.assertIn("prompt_type",card)
            self.assertIn("purpose",card)
            self.assertIn("required_fields",card)
            self.assertIn("forbidden_outputs",card)
            self.assertIn("cannot_conclude_rules",card)
            self.assertIn("source_url",card["required_fields"])
            self.assertTrue(card["research_only"])
            self.assertTrue(card["not_investment_advice"])

    def test_prompt_card_forbidden_outputs(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_scout_prompt_cards
        c = build_scout_prompt_cards()
        for card in c["phase182_prompt_cards"]["prompt_cards"]:
            self.assertIn("buy",card["forbidden_outputs"])
            self.assertIn("target_price",card["forbidden_outputs"])
            self.assertIn("position_size",card["forbidden_outputs"])

class TestPhase182TickerPlan(unittest.TestCase):
    def test_ticker_scout_plans(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_ticker_specific_prompt_plan
        p = build_ticker_specific_prompt_plan()
        tp = p["phase182_ticker_scout_plan"]
        self.assertEqual(tp["ticker_scout_plan_count"],9)
        self.assertEqual(tp["activated_candidate_count"],9)
        self.assertTrue(tp["all_plans_designed_not_dispatched"])
        for plan in tp["ticker_scout_plans"]:
            self.assertEqual(plan["prompt_type_count"],8)
            self.assertTrue(plan["auto_dispatch_disabled"])
            self.assertTrue(plan["research_only"])

class TestPhase182SourceCategoryMap(unittest.TestCase):
    def test_source_categories(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_source_category_map
        s = build_source_category_map()
        sc = s["phase182_source_category_map"]
        self.assertEqual(sc["source_category_count"],5)
        categories = [c["category"] for c in sc["source_categories"]]
        self.assertIn("official_filing",categories)
        self.assertIn("company_ir",categories)
        self.assertIn("social_or_forum",categories)

class TestPhase182DirtySchema(unittest.TestCase):
    def test_dirty_item_schema(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_dirty_intelligence_item_schema
        d = build_dirty_intelligence_item_schema()
        ds = d["phase182_dirty_item_schema"]["dirty_item_schema"]
        self.assertIn("item_id",ds["required_fields"])
        self.assertIn("source_url",ds["required_fields"])
        self.assertIn("needs_cleaning",ds["required_fields"])
        self.assertIn("buy_signal",ds["forbidden_fields"])
        self.assertIn("target_price",ds["forbidden_fields"])

class TestPhase182OutputContract(unittest.TestCase):
    def test_output_contract(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_scout_output_contract
        o = build_scout_output_contract()
        oc = o["phase182_output_contract"]
        self.assertEqual(oc["contract_version"],"1.0")
        self.assertTrue(oc["contract_not_investment_advice"])
        self.assertIn("contains_trade_terms",oc["rejection_rules"])

class TestPhase182SafetyRules(unittest.TestCase):
    def test_safety_rules(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_prompt_safety_rules
        s = build_prompt_safety_rules()
        sr = s["phase182_prompt_safety_rules"]
        self.assertGreater(sr["safety_rule_count"],10)
        self.assertTrue(sr["all_prompts_compliant"])

class TestPhase182CCRules(unittest.TestCase):
    def test_cc_rules(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_prompt_cannot_conclude_rules
        c = build_prompt_cannot_conclude_rules()
        cc = c["phase182_prompt_cc_rules"]
        self.assertGreater(cc["rule_count"],5)
        self.assertIn("cannot_conclude_investment_decision",cc["cannot_conclude_rules"])

class TestPhase182Scheduling(unittest.TestCase):
    def test_scheduling_policy(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_prompt_scheduling_policy
        s = build_prompt_scheduling_policy()
        sp = s["phase182_scheduling_policy"]
        self.assertFalse(sp["cron_enabled"])
        self.assertTrue(sp["auto_dispatch_disabled"])
        self.assertTrue(sp["scheduler_registration_disabled"])

class TestPhase182Priority(unittest.TestCase):
    def test_priority_policy(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_prompt_priority_policy
        p = build_prompt_priority_policy()
        pp = p["phase182_priority_policy"]
        self.assertIn("high",pp["priority_levels"])
        self.assertEqual(pp["default_priority"],"standard")
        self.assertIn("filing_official_source_scout",pp["high_priority_prompts"])

class TestPhase182Examples(unittest.TestCase):
    def test_expected_output_examples(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_expected_output_examples
        e = build_expected_output_examples()
        self.assertEqual(e["phase182_expected_output_examples"]["example_count"],3)
        self.assertTrue(e["phase182_expected_output_examples"]["examples_are_designed_not_real"])

    def test_invalid_output_examples(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_invalid_output_examples
        i = build_invalid_output_examples()
        self.assertEqual(i["phase182_invalid_output_examples"]["invalid_example_count"],6)
        quarantines = [ex["quarantine_reason"] for ex in i["phase182_invalid_output_examples"]["invalid_examples"]]
        self.assertIn("contains_trade_terms_and_target_price",quarantines)

class TestPhase182DirtyInbox(unittest.TestCase):
    def test_dirty_inbox_preview(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_dirty_inbox_interface_preview
        d = build_dirty_inbox_interface_preview()
        di = d["phase182_dirty_inbox_interface"]
        self.assertTrue(di["interface_preview_generated"])
        self.assertTrue(di["interface_is_preview_not_operational"])
        self.assertTrue(di["auto_ingest_disabled"])
        self.assertTrue(di["inbox_path_ignored"])

class TestPhase182Console(unittest.TestCase):
    def test_console_integration(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_console_integration
        c = build_console_integration()
        ci = c["phase182_console_integration"]
        self.assertTrue(ci["prompt_pack_viewable"])
        self.assertTrue(ci["console_not_auto_dispatch"])

class TestPhase182Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_phase182_guard
        g = build_phase182_guard()
        self.assertEqual(g["phase182_guard"]["status"],"pass")
        self.assertTrue(g["phase182_guard"]["llm_api_disabled"])
        self.assertTrue(g["phase182_guard"]["web_search_disabled"])
        self.assertTrue(g["phase182_guard"]["raw_save_disabled"])

    def test_quality_gate(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_phase182_quality_gate
        q = build_phase182_quality_gate()
        self.assertEqual(q["phase182_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase182_quality_gate"]["violations"],0)
        self.assertTrue(q["phase182_quality_gate"]["checks"]["no_llm_call"])
        self.assertTrue(q["phase182_quality_gate"]["checks"]["no_raw_save"])

    def test_cc_guard(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_phase182_cannot_conclude_guard
        c = build_phase182_cannot_conclude_guard()
        self.assertEqual(c["phase182_cannot_conclude_guard"]["status"],"pass")
        self.assertEqual(c["phase182_cannot_conclude_guard"]["violations"],0)

class TestPhase182Backlog(unittest.TestCase):
    def test_backlog(self):
        from smr_phase182_intelligence_scout_prompt_pack import build_backlog
        b = build_backlog()
        self.assertTrue(b["phase182_backlog"]["phase182_completed"])
        self.assertTrue(b["phase182_backlog"]["prompt_pack_designed"])

class TestPhase182Reporting(unittest.TestCase):
    def test_prompt_pack_board(self):
        from build_phase182_prompt_pack_board import build_prompt_pack_board
        b = build_prompt_pack_board()
        self.assertEqual(b["phase182_prompt_pack_board"]["guard"],"pass")
        self.assertEqual(b["phase182_prompt_pack_board"]["violations"],0)

    def test_prompt_pack_brief(self):
        from build_phase182_prompt_pack_board import build_prompt_pack_brief
        br = build_prompt_pack_brief()
        self.assertTrue(br["phase182_prompt_pack_brief"]["dirty_inbox_is_preview"])
        self.assertTrue(br["phase182_prompt_pack_brief"]["auto_dispatch_disabled"])

    def test_dashboard(self):
        from build_phase182_prompt_pack_board import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase182_dashboard"]["summary"]["guard"],"pass")
        self.assertEqual(d["phase182_dashboard"]["summary"]["pending_created"],0)

class TestPhase182Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase182_intelligence_scout_prompt_pack import run_pipeline
        r = run_pipeline("dry-run")
        p = r["phase182_intelligence_scout_prompt_pack_pipeline"]
        self.assertEqual(p["mode"],"dry-run")
        self.assertEqual(p["guard"],"pass")
        self.assertEqual(p["violations"],0)
        self.assertEqual(p["activated_candidate_count"],9)
        self.assertEqual(p["prompt_card_count"],8)
        self.assertFalse(p["llm_api_called"])

    def test_execute(self):
        from run_phase182_intelligence_scout_prompt_pack import run_pipeline
        r = run_pipeline("execute")
        p = r["phase182_intelligence_scout_prompt_pack_pipeline"]
        self.assertEqual(p["mode"],"execute")
        self.assertEqual(p["quality_gate"],"pass")
        self.assertEqual(p["cannot_conclude_guard"],"pass")
        self.assertEqual(p["trade_recommendation_created"],0)
        self.assertEqual(p["target_price_created"],0)
        self.assertEqual(p["position_sizing_created"],0)

    def test_skip_network(self):
        from run_phase182_intelligence_scout_prompt_pack import run_pipeline
        r = run_pipeline("skip-network")
        p = r["phase182_intelligence_scout_prompt_pack_pipeline"]
        self.assertEqual(p["mode"],"skip-network")
        self.assertEqual(p["guard"],"pass")
        self.assertFalse(p["broker_api_called"])

class TestPhase182Safety(unittest.TestCase):
    def test_no_llm_web_raw(self):
        from run_phase182_intelligence_scout_prompt_pack import run_pipeline
        for mode in ["dry-run","execute","skip-network"]:
            r = run_pipeline(mode)
            p = r["phase182_intelligence_scout_prompt_pack_pipeline"]
            self.assertFalse(p["llm_api_called"],f"llm should be false in {mode}")
            self.assertFalse(p["web_search_called"],f"web_search should be false in {mode}")
            self.assertFalse(p["network_fetch_called"],f"network_fetch should be false in {mode}")
            self.assertFalse(p["raw_saved"],f"raw_saved should be false in {mode}")
            self.assertFalse(p["clean_evidence_written"],f"clean_evidence should be false in {mode}")
            self.assertFalse(p["packet_updated"],f"packet should not be updated in {mode}")
            self.assertTrue(p["auto_dispatch_disabled"],f"auto_dispatch should be disabled in {mode}")

    def test_no_trade(self):
        from run_phase182_intelligence_scout_prompt_pack import run_pipeline
        r = run_pipeline("execute")
        p = r["phase182_intelligence_scout_prompt_pack_pipeline"]
        self.assertEqual(p["trade_recommendation_created"],0)
        self.assertEqual(p["target_price_created"],0)
        self.assertEqual(p["position_sizing_created"],0)
        self.assertEqual(p["pending_created"],0)
        self.assertEqual(p["paper_order_created"],0)
        self.assertEqual(p["real_trade_created"],0)

if __name__=="__main__":
    unittest.main()

