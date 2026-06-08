import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase185Registry(unittest.TestCase):
    def test_registry(self):
        from smr_phase185_cross_check_gate import build_cross_check_domain_registry
        r = build_cross_check_domain_registry()
        reg = r["phase185_cross_check_registry"]
        self.assertTrue(reg["registry_defined"]); self.assertEqual(reg["needs_cross_check_count"],8)
        self.assertFalse(reg["direct_cleaning_eligible"]); self.assertEqual(reg["candidate_evidence_count"],0)

class TestPhase185TaskSchema(unittest.TestCase):
    def test_schema(self):
        from smr_phase185_cross_check_gate import build_cross_check_task_schema
        s = build_cross_check_task_schema()
        self.assertIn("task_id",s["phase185_cross_check_task_schema"]["schema"])
        self.assertTrue(s["phase185_cross_check_task_schema"]["schema"]["task_not_executed"])

class TestPhase185Reasons(unittest.TestCase):
    def test_reasons(self):
        from smr_phase185_cross_check_gate import build_cross_check_reason_classifier
        r = build_cross_check_reason_classifier()
        self.assertEqual(r["phase185_cross_check_reasons"]["items_checked"],8)
        for item in r["phase185_cross_check_reasons"]["results"]:
            self.assertIn("cross_check_reason_type",item)

class TestPhase185SourceRoutes(unittest.TestCase):
    def test_source_routes(self):
        from smr_phase185_cross_check_gate import build_source_route_builder
        s = build_source_route_builder()
        self.assertEqual(s["phase185_source_routes"]["route_count"],8)
        self.assertTrue(s["phase185_source_routes"]["all_routes_designed_not_executed"])
        for r in s["phase185_source_routes"]["routes"]:
            self.assertTrue(r["source_route_not_network_fetch"])
            self.assertGreaterEqual(len(r["recommended_sources"]),1)

class TestPhase185PromptRoutes(unittest.TestCase):
    def test_prompt_routes(self):
        from smr_phase185_cross_check_gate import build_prompt_route_builder
        p = build_prompt_route_builder()
        self.assertEqual(p["phase185_prompt_routes"]["route_count"],8)
        self.assertTrue(p["phase185_prompt_routes"]["all_routes_designed_not_called"])
        for r in p["phase185_prompt_routes"]["routes"]:
            self.assertTrue(r["prompt_route_not_llm_call"])

class TestPhase185Verification(unittest.TestCase):
    def test_verification_requirements(self):
        from smr_phase185_cross_check_gate import build_verification_requirement_builder
        v = build_verification_requirement_builder()
        self.assertEqual(v["phase185_verification_requirements"]["requirement_count"],8)
        self.assertTrue(v["phase185_verification_requirements"]["all_requirements_designed_not_verified"])

class TestPhase185Policies(unittest.TestCase):
    def test_independent_source_policy(self):
        from smr_phase185_cross_check_gate import build_independent_source_policy
        p = build_independent_source_policy()
        self.assertEqual(p["phase185_independent_source_policy"]["minimum_independent_sources"],2)
        self.assertEqual(p["phase185_independent_source_policy"]["social_or_forum_minimum"],3)

    def test_source_diversity_policy(self):
        from smr_phase185_cross_check_gate import build_source_diversity_policy
        p = build_source_diversity_policy()
        self.assertTrue(p["phase185_source_diversity_policy"]["at_least_one_official_source_required"])

class TestPhase185Tasks(unittest.TestCase):
    def test_tasks(self):
        from smr_phase185_cross_check_gate import build_cross_check_tasks
        t = build_cross_check_tasks()
        self.assertEqual(t["phase185_cross_check_tasks"]["task_count"],8)
        self.assertTrue(t["phase185_cross_check_tasks"]["all_tasks_designed_not_executed"])
        self.assertTrue(t["phase185_cross_check_tasks"]["tasks_do_not_create_clean_evidence"])
        for task in t["phase185_cross_check_tasks"]["tasks"]:
            self.assertTrue(task["task_not_executed"]); self.assertTrue(task["task_not_network_fetch"])
            self.assertTrue(task["task_not_llm_call"]); self.assertTrue(task["task_not_clean_evidence"])

class TestPhase185Gate(unittest.TestCase):
    def test_eligibility_gate(self):
        from smr_phase185_cross_check_gate import build_eligibility_gate
        g = build_eligibility_gate()
        gt = g["phase185_eligibility_gate"]
        self.assertTrue(gt["eligibility_gate_active"]); self.assertFalse(gt["direct_cleaning_eligible"])
        self.assertEqual(gt["blocked_pending_cross_check_count"],8); self.assertTrue(gt["gate_blocks_dirty_items"])
        self.assertTrue(gt["gate_is_not_clean_evidence_write"]); self.assertTrue(gt["gate_prevents_premature_cleaning"])

class TestPhase185Readiness(unittest.TestCase):
    def test_cleaning_readiness(self):
        from smr_phase185_cross_check_gate import build_cleaning_readiness_preview
        c = build_cleaning_readiness_preview()
        self.assertEqual(c["phase185_cleaning_readiness_preview"]["items_ready_for_cleaning"],0)
        self.assertTrue(c["phase185_cleaning_readiness_preview"]["cleaning_not_started"])
        self.assertTrue(c["phase185_cleaning_readiness_preview"]["auto_clean_disabled"])

class TestPhase185Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase185_cross_check_gate import build_phase185_guard
        g = build_phase185_guard()
        self.assertEqual(g["phase185_guard"]["status"],"pass")
        self.assertTrue(g["phase185_guard"]["clean_evidence_write_disabled"])
        self.assertTrue(g["phase185_guard"]["cross_check_execution_disabled"])

    def test_quality_gate(self):
        from smr_phase185_cross_check_gate import build_phase185_quality_gate
        q = build_phase185_quality_gate()
        self.assertEqual(q["phase185_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase185_quality_gate"]["violations"],0)
        self.assertTrue(q["phase185_quality_gate"]["checks"]["gate_blocks_dirty_to_clean"])

    def test_cc_guard(self):
        from smr_phase185_cross_check_gate import build_phase185_cannot_conclude_guard
        c = build_phase185_cannot_conclude_guard()
        self.assertEqual(c["phase185_cannot_conclude_guard"]["status"],"pass")
        self.assertIn("cross_check_task_is_not_cross_check_execution",c["phase185_cannot_conclude_guard"]["cannot_conclude"])

class TestPhase185Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase185_cross_check_board import build_cross_check_board
        b = build_cross_check_board()
        self.assertEqual(b["phase185_cross_check_board"]["guard"],"pass")
    def test_brief(self):
        from build_phase185_cross_check_board import build_cross_check_brief
        br = build_cross_check_brief()
        self.assertEqual(br["phase185_cross_check_brief"]["task_count"],8)
        self.assertTrue(br["phase185_cross_check_brief"]["gate_blocks_premature_cleaning"])
    def test_dashboard(self):
        from build_phase185_cross_check_board import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase185_dashboard"]["summary"]["guard"],"pass")

class TestPhase185Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase185_cross_check_gate import run_pipeline
        r = run_pipeline("dry-run")
        p = r["phase185_cross_check_gate_pipeline"]
        self.assertEqual(p["mode"],"dry-run"); self.assertEqual(p["guard"],"pass")
        self.assertEqual(p["cross_check_task_count"],8); self.assertTrue(p["tasks_not_executed"])

    def test_execute(self):
        from run_phase185_cross_check_gate import run_pipeline
        r = run_pipeline("execute")
        p = r["phase185_cross_check_gate_pipeline"]
        self.assertTrue(p["gate_not_clean_evidence_write"]); self.assertTrue(p["gate_blocks_premature_cleaning"])
        self.assertEqual(p["blocked_pending_cross_check"],8)

    def test_skip_network(self):
        from run_phase185_cross_check_gate import run_pipeline
        r = run_pipeline("skip-network")
        p = r["phase185_cross_check_gate_pipeline"]
        self.assertEqual(p["mode"],"skip-network"); self.assertEqual(p["quality_gate"],"pass")

class TestPhase185Safety(unittest.TestCase):
    def test_no_llm_clean(self):
        from run_phase185_cross_check_gate import run_pipeline
        for mode in ["dry-run","execute","skip-network"]:
            r = run_pipeline(mode); p = r["phase185_cross_check_gate_pipeline"]
            self.assertFalse(p["llm_api_called"]); self.assertFalse(p["web_search_called"])
            self.assertFalse(p["clean_evidence_written"]); self.assertFalse(p["packet_updated"])
    def test_no_trade(self):
        from run_phase185_cross_check_gate import run_pipeline
        r = run_pipeline("execute")
        p = r["phase185_cross_check_gate_pipeline"]
        self.assertEqual(p["trade_recommendation_created"],0); self.assertEqual(p["target_price_created"],0)
        self.assertEqual(p["position_sizing_created"],0); self.assertEqual(p["pending_created"],0)

if __name__=="__main__": unittest.main()

