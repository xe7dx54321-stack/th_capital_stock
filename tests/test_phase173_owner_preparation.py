import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase173Config(unittest.TestCase):
    def test_config(self):
        from smr_phase173_config import load_phase173_config
        c = load_phase173_config()
        self.assertEqual(c["phase"], "phase173")
        self.assertTrue(c["candidate_recommendation_draft_enabled"])
        self.assertFalse(c["auto_write_real_input"])
        self.assertFalse(c["auto_execute_apply"])

class TestPhase173Core(unittest.TestCase):
    def test_recommendations(self):
        from smr_phase173_core import build_candidate_recommendation_draft
        r = build_candidate_recommendation_draft()
        rec = r["phase173_candidate_recommendation_draft"]
        self.assertEqual(rec["entries"], 13)
        self.assertEqual(rec["activated"]+rec["kept"]+rec["deferred"]+rec["rejected"], 13)
        self.assertTrue(rec["recommendation_not_approval"])
    def test_json_draft(self):
        from smr_phase173_core import build_fill_ready_json_draft
        r = build_fill_ready_json_draft()
        self.assertTrue(r["phase173_fill_ready_json_draft"]["draft_generated"])
        self.assertTrue(r["phase173_fill_ready_json_draft"]["draft_not_real_input"])
        self.assertTrue(r["phase173_fill_ready_json_draft"]["auto_write_disabled"])
    def test_checklist(self):
        from smr_phase173_core import build_preflight_checklist
        r = build_preflight_checklist()
        self.assertEqual(r["phase173_preflight_checklist"]["item_count"], 14)
    def test_instructions(self):
        from smr_phase173_core import build_execute_apply_instructions
        r = build_execute_apply_instructions()
        self.assertTrue(r["phase173_execute_apply_instructions"]["DO_NOT_auto_execute"])

class TestPhase173Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase173_guard import build_owner_preparation_guard
        r = build_owner_preparation_guard()
        self.assertEqual(r["phase173_owner_preparation_guard"]["status"], "pass")
    def test_cc(self):
        from smr_phase173_guard import build_cannot_conclude_guard
        r = build_cannot_conclude_guard()
        self.assertIn("recommendation_is_not_owner_decision", r["phase173_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase173Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase173_owner_preparation_board import build
        r = build()
        self.assertEqual(r["phase173_owner_preparation_board"]["guard"], "pass")
    def test_dashboard(self):
        from build_phase173_owner_preparation_dashboard import build_dashboard
        r = build_dashboard()
        self.assertEqual(r["phase173_owner_preparation_dashboard"]["summary"]["guard"], "pass")

class TestPhase173Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase173_owner_preparation_pipeline import run
        r = run("dry-run")
        self.assertEqual(r["phase173_owner_preparation_pipeline"]["guard"], "pass")
        self.assertTrue(r["phase173_owner_preparation_pipeline"]["draft_not_real_input"])

if __name__ == "__main__":
    unittest.main()
