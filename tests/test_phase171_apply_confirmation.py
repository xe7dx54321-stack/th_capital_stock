import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase171Config(unittest.TestCase):
    def test_config(self):
        from smr_phase171_config import load_phase171_config
        c = load_phase171_config()
        self.assertEqual(c["phase"], "phase171")
        self.assertTrue(c["apply_confirmation_gate_enabled"])
        self.assertFalse(c["real_state_update_allowed"])

class TestPhase171Core(unittest.TestCase):
    def setUp(self):
        from smr_phase170_validator import validate_owner_input
        inp = {"decisions":[{"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage","rationale":"Evidence complete.","conditions":["x"],"risk_acknowledgment":"ok"},{"candidate_id":"AMAT","owner_decision":"keep_as_candidate_pending_more_evidence","rationale":"Pending.","conditions":["x"],"risk_acknowledgment":"ok"}]}
        self.v = validate_owner_input(inp)
    def test_apply_gate(self):
        from smr_phase171_core import build_apply_confirmation_gate
        r = build_apply_confirmation_gate(self.v)
        self.assertTrue(r["phase171_apply_confirmation_gate"]["ready_for_apply"])
        self.assertTrue(r["phase171_apply_confirmation_gate"]["apply_not_executed"])
    def test_apply_package(self):
        from smr_phase171_core import build_coverage_apply_package
        r = build_coverage_apply_package(self.v)
        self.assertEqual(r["phase171_coverage_apply_package"]["activated_count"], 1)
        self.assertEqual(r["phase171_coverage_apply_package"]["kept_count"], 1)
        self.assertTrue(r["phase171_coverage_apply_package"]["apply_not_executed"])
    def test_state_diff(self):
        from smr_phase171_core import build_state_diff
        r = build_state_diff(self.v)
        self.assertTrue(r["phase171_state_diff"]["state_not_updated"])
    def test_rollback(self):
        from smr_phase171_core import build_rollback_package
        r = build_rollback_package()
        self.assertTrue(r["phase171_rollback_package"]["rollback_prepared"])
    def test_checklist(self):
        from smr_phase171_core import build_final_checklist
        r = build_final_checklist()
        self.assertEqual(r["phase171_final_checklist"]["item_count"], 9)

class TestPhase171Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase170_validator import validate_owner_input
        from smr_phase171_core import build_apply_confirmation_gate
        from smr_phase171_guard import build_apply_confirmation_guard
        v = validate_owner_input(None); g = build_apply_confirmation_gate(v)
        r = build_apply_confirmation_guard(g)
        self.assertEqual(r["phase171_apply_confirmation_guard"]["status"], "pass")
    def test_quality_gate(self):
        from smr_phase170_validator import validate_owner_input
        from smr_phase171_core import build_apply_confirmation_gate, build_coverage_apply_package
        from smr_phase171_guard import build_quality_gate
        v = validate_owner_input(None); ap = build_coverage_apply_package(v); g = build_apply_confirmation_gate(v)
        r = build_quality_gate(ap, g)
        self.assertEqual(r["phase171_quality_gate"]["status"], "pass")
    def test_cc(self):
        from smr_phase171_guard import build_cannot_conclude_guard
        r = build_cannot_conclude_guard()
        self.assertIn("300394 CNINFO org_id missing", r["phase171_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase171Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase171_apply_confirmation_board import build
        r = build()
        self.assertEqual(r["phase171_apply_confirmation_board"]["guard"], "pass")
    def test_dashboard(self):
        from build_phase171_apply_confirmation_dashboard import build_dashboard
        r = build_dashboard()
        self.assertEqual(r["phase171_apply_confirmation_dashboard"]["summary"]["guard"], "pass")

class TestPhase171Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase171_apply_confirmation_pipeline import run
        r = run("dry-run")
        p = r["phase171_apply_confirmation_pipeline"]
        self.assertEqual(p["guard"], "pass")
        self.assertTrue(p["apply_not_executed"])
    def test_execute(self):
        from run_phase171_apply_confirmation_pipeline import run
        self.assertEqual(run("execute")["phase171_apply_confirmation_pipeline"]["guard"], "pass")
    def test_skip(self):
        from run_phase171_apply_confirmation_pipeline import run
        self.assertEqual(run("skip-network")["phase171_apply_confirmation_pipeline"]["guard"], "pass")

if __name__ == "__main__":
    unittest.main()
