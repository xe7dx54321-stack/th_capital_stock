import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase186Registry(unittest.TestCase):
    def test_registry(self):
        from smr_phase186_simulated_scout_cross_check import build_simulated_scout_registry
        r = build_simulated_scout_registry()
        reg = r["phase186_simulated_scout_registry"]
        self.assertTrue(reg["simulated_only"]); self.assertEqual(reg["input_tasks"],8)
        self.assertTrue(reg["no_real_llm"]); self.assertTrue(reg["no_real_web"])

class TestPhase186Observations(unittest.TestCase):
    def test_schema(self):
        from smr_phase186_simulated_scout_cross_check import build_simulated_source_observation_schema
        s = build_simulated_source_observation_schema()
        self.assertIn("buy_signal",s["phase186_observation_schema"]["forbidden_fields"])
        self.assertTrue(s["phase186_observation_schema"]["simulated_only"])

    def test_generator(self):
        from smr_phase186_simulated_scout_cross_check import build_simulated_scout_output_generator
        o = build_simulated_scout_output_generator()
        self.assertGreater(o["phase186_simulated_observations"]["observation_count"],8)
        self.assertTrue(o["phase186_simulated_observations"]["all_simulated"])
        self.assertTrue(o["phase186_simulated_observations"]["all_not_real_source"])
        for obs in o["phase186_simulated_observations"]["observations"]:
            self.assertTrue(obs["simulated"]); self.assertTrue(obs["not_real_source"])
            self.assertTrue(obs["not_verified_evidence"]); self.assertTrue(obs["llm_not_called"])

class TestPhase186Runner(unittest.TestCase):
    def test_runner(self):
        from smr_phase186_simulated_scout_cross_check import build_cross_check_runner
        r = build_cross_check_runner()
        rr = r["phase186_cross_check_runner"]
        self.assertEqual(rr["run_count"],8); self.assertTrue(rr["all_runs_simulated"])
        self.assertTrue(rr["all_runs_not_real"]); self.assertTrue(rr["no_real_verification"])
        for run in rr["runs"]:
            self.assertTrue(run["run_not_real_execution"]); self.assertTrue(run["run_not_network_fetch"])

class TestPhase186Previews(unittest.TestCase):
    def test_source_match(self):
        from smr_phase186_simulated_scout_cross_check import build_source_match_preview
        s = build_source_match_preview()
        self.assertEqual(s["phase186_source_match_preview"]["match_count"],8)
        self.assertTrue(s["phase186_source_match_preview"]["all_matches_simulated"])

    def test_verification(self):
        from smr_phase186_simulated_scout_cross_check import build_verification_result_preview
        v = build_verification_result_preview()
        self.assertEqual(v["phase186_verification_preview"]["result_count"],8)
        self.assertTrue(v["phase186_verification_preview"]["all_results_simulated"])

class TestPhase186Outcome(unittest.TestCase):
    def test_classifier(self):
        from smr_phase186_simulated_scout_cross_check import build_outcome_classifier
        c = build_outcome_classifier()
        self.assertEqual(c["phase186_outcome_classifier"]["classified_count"],8)

    def test_manifest(self):
        from smr_phase186_simulated_scout_cross_check import build_outcome_manifest
        m = build_outcome_manifest()
        self.assertTrue(m["phase186_outcome_manifest"]["manifest_generated"])
        self.assertTrue(m["phase186_outcome_manifest"]["manifest_does_not_create_clean_evidence"])
        self.assertTrue(m["phase186_outcome_manifest"]["simulated_only"])

class TestPhase186Eligibility(unittest.TestCase):
    def test_refresh(self):
        from smr_phase186_simulated_scout_cross_check import build_eligibility_refresh
        e = build_eligibility_refresh()
        self.assertTrue(e["phase186_eligibility_refresh"]["would_be_ready_is_not_clean_evidence"])
        self.assertTrue(e["phase186_eligibility_refresh"]["would_be_ready_requires_real_verification"])
        self.assertTrue(e["phase186_eligibility_refresh"]["simulated_only_not_real_eligible"])

    def test_cleaning_readiness(self):
        from smr_phase186_simulated_scout_cross_check import build_cleaning_readiness_refresh
        c = build_cleaning_readiness_refresh()
        self.assertTrue(c["phase186_cleaning_readiness_refresh"]["simulated_readiness_not_real_cleaning"])
        self.assertTrue(c["phase186_cleaning_readiness_refresh"]["would_be_ready_requires_real_verification_first"])

class TestPhase186Failure(unittest.TestCase):
    def test_handler(self):
        from smr_phase186_simulated_scout_cross_check import build_failure_handler
        f = build_failure_handler()
        self.assertTrue(f["phase186_failure_handler"]["handler_active"])
        self.assertTrue(f["phase186_failure_handler"]["simulated_failures_only"])
        self.assertTrue(f["phase186_failure_handler"]["auto_retry_disabled"])

class TestPhase186Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase186_simulated_scout_cross_check import build_phase186_guard
        g = build_phase186_guard()
        self.assertEqual(g["phase186_guard"]["status"],"pass")
        self.assertTrue(g["phase186_guard"]["simulated_only"])

    def test_quality_gate(self):
        from smr_phase186_simulated_scout_cross_check import build_phase186_quality_gate
        q = build_phase186_quality_gate()
        self.assertEqual(q["phase186_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase186_quality_gate"]["violations"],0)

    def test_cc_guard(self):
        from smr_phase186_simulated_scout_cross_check import build_phase186_cannot_conclude_guard
        c = build_phase186_cannot_conclude_guard()
        self.assertEqual(c["phase186_cannot_conclude_guard"]["status"],"pass")
        self.assertIn("simulated_observation_is_not_real_source",c["phase186_cannot_conclude_guard"]["cannot_conclude"])

class TestPhase186Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase186_cross_check_runner_board import build_runner_board
        b = build_runner_board()
        self.assertEqual(b["phase186_cross_check_runner_board"]["guard"],"pass")
    def test_brief(self):
        from build_phase186_cross_check_runner_board import build_runner_brief
        br = build_runner_brief()
        self.assertTrue(br["phase186_cross_check_runner_brief"]["simulated_only"])
    def test_dashboard(self):
        from build_phase186_cross_check_runner_board import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase186_dashboard"]["summary"]["guard"],"pass")

class TestPhase186Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase186_simulated_scout_cross_check import run_pipeline
        r = run_pipeline("dry-run")
        p = r["phase186_simulated_scout_cross_check_pipeline"]
        self.assertEqual(p["mode"],"dry-run"); self.assertEqual(p["guard"],"pass")
        self.assertTrue(p["simulated"]); self.assertEqual(p["cross_check_task_count"],8)

    def test_execute(self):
        from run_phase186_simulated_scout_cross_check import run_pipeline
        r = run_pipeline("execute")
        p = r["phase186_simulated_scout_cross_check_pipeline"]
        self.assertTrue(p["simulated_observation_not_real_source"])
        self.assertTrue(p["would_be_ready_not_clean_evidence_now"])
        self.assertFalse(p["clean_evidence_written"])

    def test_skip_network(self):
        from run_phase186_simulated_scout_cross_check import run_pipeline
        r = run_pipeline("skip-network")
        p = r["phase186_simulated_scout_cross_check_pipeline"]
        self.assertEqual(p["mode"],"skip-network"); self.assertEqual(p["quality_gate"],"pass")

class TestPhase186Safety(unittest.TestCase):
    def test_no_llm_clean(self):
        from run_phase186_simulated_scout_cross_check import run_pipeline
        for mode in ["dry-run","execute","skip-network"]:
            r = run_pipeline(mode); p = r["phase186_simulated_scout_cross_check_pipeline"]
            self.assertFalse(p["llm_api_called"]); self.assertFalse(p["web_search_called"])
            self.assertFalse(p["clean_evidence_written"])
    def test_no_trade(self):
        from run_phase186_simulated_scout_cross_check import run_pipeline
        r = run_pipeline("execute")
        p = r["phase186_simulated_scout_cross_check_pipeline"]
        self.assertEqual(p["trade_recommendation_created"],0); self.assertEqual(p["target_price_created"],0)

if __name__=="__main__": unittest.main()
