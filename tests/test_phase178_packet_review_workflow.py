import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase178Console(unittest.TestCase):
    def test_console_generated(self):
        from smr_phase178_review_workflow import build_review_console
        c = build_review_console()
        self.assertTrue(c["phase178_review_console"]["console_generated"])
        self.assertEqual(c["phase178_review_console"]["review_cards_count"],9)

    def test_cards_have_correct_fields(self):
        from smr_phase178_review_workflow import build_review_console
        c = build_review_console()
        for card in c["phase178_review_console"]["review_cards"]:
            self.assertIn("candidate_id",card)
            self.assertIn("review_status",card)
            self.assertEqual(card["review_status"],"pending_owner_review")
            self.assertTrue(card["review_not_thesis_confirmed"])

class TestPhase178Templates(unittest.TestCase):
    def test_templates_generated(self):
        from smr_phase178_review_workflow import build_review_templates
        t = build_review_templates()
        self.assertIn("input_template",t["phase178_review_templates"])
        self.assertIn("signoff_template",t["phase178_review_templates"])
        self.assertIn("revision_template",t["phase178_review_templates"])

    def test_auto_write_disabled(self):
        from smr_phase178_review_workflow import build_review_templates
        t = build_review_templates()
        self.assertTrue(t["phase178_review_templates"]["input_template"]["auto_write_disabled"])
        self.assertFalse(t["phase178_review_templates"]["signoff_template"]["auto_signoff_allowed"])

class TestPhase178Tracker(unittest.TestCase):
    def test_tracker(self):
        from smr_phase178_review_workflow import build_review_status_tracker
        t = build_review_status_tracker()
        tr = t["phase178_review_status_tracker"]
        self.assertEqual(tr["total"],9)
        self.assertEqual(tr["pending_owner_review"],9)
        self.assertEqual(tr["review_state"],"no_owner_review_input_pending")

class TestPhase178Gates(unittest.TestCase):
    def test_daily_gate(self):
        from smr_phase178_review_workflow import build_daily_brief_preview_gate
        d = build_daily_brief_preview_gate()
        self.assertEqual(d["phase178_daily_brief_preview_gate"]["gate_status"],"waiting_owner_review")
        self.assertTrue(d["phase178_daily_brief_preview_gate"]["preview_is_not_trade_signal"])

    def test_weekly_gate(self):
        from smr_phase178_review_workflow import build_weekly_review_preview_gate
        w = build_weekly_review_preview_gate()
        self.assertEqual(w["phase178_weekly_review_preview_gate"]["gate_status"],"waiting_owner_review")

class TestPhase178Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase178_review_workflow import build_phase178_guard
        g = build_phase178_guard()
        self.assertEqual(g["phase178_guard"]["status"],"pass")

    def test_quality_gate(self):
        from smr_phase178_review_workflow import build_phase178_quality_gate
        q = build_phase178_quality_gate()
        self.assertEqual(q["phase178_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase178_quality_gate"]["violations"],0)

    def test_cc(self):
        from smr_phase178_review_workflow import build_phase178_cannot_conclude_guard
        c = build_phase178_cannot_conclude_guard()
        self.assertEqual(c["phase178_cannot_conclude_guard"]["status"],"pass")

class TestPhase178Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase178_review_board import build_review_board
        b = build_review_board()
        self.assertTrue(b["phase178_review_board"]["review_console"]["console_generated"])

    def test_dashboard(self):
        from build_phase178_review_board import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase178_dashboard"]["summary"]["packet_count"],9)

class TestPhase178Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase178_packet_review_workflow import run_pipeline
        r = run_pipeline("dry-run")
        self.assertEqual(r["phase178_packet_review_pipeline"]["mode"],"dry-run")
        self.assertEqual(r["phase178_packet_review_pipeline"]["guard"],"pass")

    def test_execute(self):
        from run_phase178_packet_review_workflow import run_pipeline
        r = run_pipeline("execute")
        self.assertEqual(r["phase178_packet_review_pipeline"]["packet_count"],9)
        self.assertFalse(r["phase178_packet_review_pipeline"]["owner_review_input_written"])

    def test_skip_network(self):
        from run_phase178_packet_review_workflow import run_pipeline
        r = run_pipeline("skip-network")
        self.assertEqual(r["phase178_packet_review_pipeline"]["mode"],"skip-network")

if __name__=="__main__":
    unittest.main()
