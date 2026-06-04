import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase181ManualDraft(unittest.TestCase):
    def test_draft_generated(self):
        from smr_phase181_authoring_pack import build_manual_draft
        d = build_manual_draft()
        md = d["phase181_manual_draft"]
        self.assertTrue(md["draft_generated"])
        self.assertTrue(md["draft_is_template"])
        self.assertTrue(md["draft_not_real_input"])
        self.assertTrue(md["auto_write_to_real_input_disabled"])
        self.assertEqual(md["packet_count"],9)
        self.assertFalse(md["mock_used"])
        self.assertFalse(md["fixture_used"])

    def test_draft_has_reviews(self):
        from smr_phase181_authoring_pack import build_manual_draft
        d = build_manual_draft()
        reviews = d["phase181_manual_draft"]["draft_json"]["reviews"]
        self.assertEqual(len(reviews),9)
        for r in reviews:
            self.assertIn("candidate_id",r)
            self.assertIn("review_status",r)
            self.assertEqual(r["review_status"],"owner_reviewed")

class TestPhase181Worksheet(unittest.TestCase):
    def test_worksheet_generated(self):
        from smr_phase181_authoring_pack import build_review_worksheet
        ws = build_review_worksheet()
        w = ws["phase181_review_worksheet"]
        self.assertGreaterEqual(w["worksheet_count"],1)
        self.assertTrue(w["worksheets"][0]["worksheet_not_auto_filled"])
        for s in w["worksheets"]:
            self.assertIn("candidate_id",s)
            self.assertIn("review_status_options",s)
            self.assertIn("owner_reviewed",s["review_status_options"])

class TestPhase181Examples(unittest.TestCase):
    def test_valid_examples(self):
        from smr_phase181_authoring_pack import build_valid_example_pack
        v = build_valid_example_pack()
        ve = v["phase181_valid_example_pack"]
        self.assertEqual(ve["valid_examples_count"],7)
        self.assertTrue(ve["examples_not_real_input"])
        self.assertFalse(ve["mock_used"])
        self.assertFalse(ve["fixture_used"])

    def test_invalid_examples(self):
        from smr_phase181_authoring_pack import build_invalid_example_pack
        iv = build_invalid_example_pack()
        ie = iv["phase181_invalid_example_pack"]
        self.assertEqual(ie["invalid_examples_count"],8)
        self.assertTrue(ie["examples_not_real_input"])
        quarantines = [e["quarantine_reason"] for e in ie["invalid_examples"]]
        self.assertIn("unknown_candidate",quarantines)
        self.assertIn("invalid_status",quarantines)
        self.assertIn("trade_term:buy",quarantines)

class TestPhase181Preflight(unittest.TestCase):
    def test_preflight_pass(self):
        from smr_phase181_authoring_pack import build_preflight_checker
        pf = build_preflight_checker()
        p = pf["phase181_preflight"]
        self.assertTrue(p["preflight_checked"])
        self.assertTrue(p["preflight_pass"])
        self.assertEqual(p["issues_found"],0)
        self.assertTrue(p["preflight_not_real_validation"])

class TestPhase181Sandbox(unittest.TestCase):
    def test_sandbox_checked(self):
        from smr_phase181_authoring_pack import build_sandbox_simulation
        sb = build_sandbox_simulation()
        self.assertTrue(sb["phase181_sandbox"]["sandbox_checked"])
        self.assertTrue(sb["phase181_sandbox"]["simulation_only"])
        self.assertTrue(sb["phase181_sandbox"]["simulation_not_real_input"])

class TestPhase181Guides(unittest.TestCase):
    def test_copy_paste_package(self):
        from smr_phase181_authoring_pack import build_copy_paste_package
        cp = build_copy_paste_package()
        self.assertTrue(cp["phase181_copy_paste_package"]["package_generated"])
        self.assertTrue(cp["phase181_copy_paste_package"]["copy_paste_not_auto_write"])

    def test_file_placement_guide(self):
        from smr_phase181_authoring_pack import build_file_placement_guide
        fg = build_file_placement_guide()
        self.assertTrue(fg["phase181_file_placement_guide"]["guide_generated"])
        self.assertTrue(fg["phase181_file_placement_guide"]["guide_not_auto_copy"])

    def test_command_guide(self):
        from smr_phase181_authoring_pack import build_command_guide
        cg = build_command_guide()
        self.assertTrue(cg["phase181_command_guide"]["guide_generated"])
        self.assertTrue(cg["phase181_command_guide"]["guide_not_auto_execute"])

class TestPhase181Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase181_authoring_pack import build_phase181_guard
        g = build_phase181_guard()
        self.assertEqual(g["phase181_guard"]["status"],"pass")
        self.assertTrue(g["phase181_guard"]["research_only"])
        self.assertTrue(g["phase181_guard"]["real_input_write_disabled"])
        self.assertTrue(g["phase181_guard"]["auto_signoff_disabled"])
        self.assertTrue(g["phase181_guard"]["draft_is_template_not_real_input"])

    def test_quality_gate(self):
        from smr_phase181_authoring_pack import build_phase181_quality_gate
        q = build_phase181_quality_gate()
        self.assertEqual(q["phase181_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase181_quality_gate"]["violations"],0)
        self.assertTrue(q["phase181_quality_gate"]["checks"]["preflight_pass"])
        self.assertTrue(q["phase181_quality_gate"]["checks"]["no_real_input_write"])

    def test_cc_guard(self):
        from smr_phase181_authoring_pack import build_phase181_cannot_conclude_guard
        c = build_phase181_cannot_conclude_guard()
        self.assertEqual(c["phase181_cannot_conclude_guard"]["status"],"pass")
        self.assertEqual(c["phase181_cannot_conclude_guard"]["violations"],0)

class TestPhase181ExpectationMatcher(unittest.TestCase):
    def test_expectations(self):
        from smr_phase181_authoring_pack import build_expectation_matcher
        em = build_expectation_matcher()
        self.assertTrue(em["phase181_expectation_matcher"]["expectations_all_match"])

class TestPhase181Console(unittest.TestCase):
    def test_console_integration(self):
        from smr_phase181_authoring_pack import build_console_authoring_integration
        ci = build_console_authoring_integration()
        self.assertTrue(ci["phase181_console_authoring_integration"]["draft_viewable"])
        self.assertTrue(ci["phase181_console_authoring_integration"]["console_not_auto_write"])

class TestPhase181Reporting(unittest.TestCase):
    def test_authoring_board(self):
        from build_phase181_authoring_board import build_authoring_board
        ab = build_authoring_board()
        self.assertEqual(ab["phase181_authoring_board"]["guard"],"pass")
        self.assertEqual(ab["phase181_authoring_board"]["violations"],0)

    def test_authoring_brief(self):
        from build_phase181_authoring_board import build_authoring_brief
        br = build_authoring_brief()
        self.assertTrue(br["phase181_authoring_brief"]["draft_ready"])
        self.assertTrue(br["phase181_authoring_brief"]["owner_must_manually_fill"])

    def test_dashboard(self):
        from build_phase181_authoring_board import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase181_dashboard"]["summary"]["guard"],"pass")
        self.assertEqual(d["phase181_dashboard"]["summary"]["pending_created"],0)

    def test_backlog_update(self):
        from build_phase181_authoring_board import build_backlog_update
        bu = build_backlog_update()
        self.assertTrue(bu["phase181_backlog_update"]["phase181_completed"])
        self.assertIn("phase182",bu["phase181_backlog_update"]["next_phases"])

class TestPhase181Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase181_owner_review_authoring_pack import run_pipeline
        r = run_pipeline("dry-run")
        self.assertEqual(r["phase181_owner_review_authoring_pack_pipeline"]["mode"],"dry-run")
        self.assertEqual(r["phase181_owner_review_authoring_pack_pipeline"]["guard"],"pass")
        self.assertEqual(r["phase181_owner_review_authoring_pack_pipeline"]["violations"],0)
        self.assertTrue(r["phase181_owner_review_authoring_pack_pipeline"]["draft_not_real_input"])
        self.assertTrue(r["phase181_owner_review_authoring_pack_pipeline"]["owner_must_manually_fill"])

    def test_execute(self):
        from run_phase181_owner_review_authoring_pack import run_pipeline
        r = run_pipeline("execute")
        self.assertEqual(r["phase181_owner_review_authoring_pack_pipeline"]["packet_count"],9)
        self.assertTrue(r["phase181_owner_review_authoring_pack_pipeline"]["preflight_pass"])
        self.assertEqual(r["phase181_owner_review_authoring_pack_pipeline"]["pending_created"],0)
        self.assertEqual(r["phase181_owner_review_authoring_pack_pipeline"]["paper_order_created"],0)
        self.assertEqual(r["phase181_owner_review_authoring_pack_pipeline"]["real_trade_created"],0)

    def test_skip_network(self):
        from run_phase181_owner_review_authoring_pack import run_pipeline
        r = run_pipeline("skip-network")
        self.assertEqual(r["phase181_owner_review_authoring_pack_pipeline"]["mode"],"skip-network")
        self.assertEqual(r["phase181_owner_review_authoring_pack_pipeline"]["quality_gate"],"pass")

class TestPhase181Safety(unittest.TestCase):
    def test_no_auto_signoff(self):
        from run_phase181_owner_review_authoring_pack import run_pipeline
        for mode in ["dry-run","execute","skip-network"]:
            r = run_pipeline(mode)
            self.assertFalse(r["phase181_owner_review_authoring_pack_pipeline"]["auto_signoff"],f"auto_signoff should be False in {mode}")
            self.assertFalse(r["phase181_owner_review_authoring_pack_pipeline"]["auto_revision"],f"auto_revision should be False in {mode}")
            self.assertFalse(r["phase181_owner_review_authoring_pack_pipeline"]["auto_publish"],f"auto_publish should be False in {mode}")

    def test_no_trade(self):
        from run_phase181_owner_review_authoring_pack import run_pipeline
        r = run_pipeline("execute")
        self.assertEqual(r["phase181_owner_review_authoring_pack_pipeline"]["target_price_created"],0)
        self.assertEqual(r["phase181_owner_review_authoring_pack_pipeline"]["trade_recommendation_created"],0)
        self.assertFalse(r["phase181_owner_review_authoring_pack_pipeline"]["broker_api_called"])

if __name__=="__main__":
    unittest.main()

