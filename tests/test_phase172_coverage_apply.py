import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase172Config(unittest.TestCase):
    def test_config(self):
        from smr_phase172_config import load_phase172_config
        c = load_phase172_config()
        self.assertEqual(c["phase"], "phase172")
        self.assertTrue(c["execute_apply_requires_explicit_flag"])
        self.assertTrue(c["coverage_state_apply_enabled"])
        self.assertFalse(c["trade_system_integration_allowed"])

class TestPhase172Core(unittest.TestCase):
    def setUp(self):
        from smr_phase170_validator import validate_owner_input
        from smr_phase171_core import build_apply_confirmation_gate, build_coverage_apply_package
        v = validate_owner_input(None); self.cg = build_apply_confirmation_gate(v); self.ap = build_coverage_apply_package(v); self.v = v
    def test_prerequisites_no_input(self):
        from smr_phase172_core import build_prerequisite_checker
        r = build_prerequisite_checker(None, self.v, self.cg, self.ap)
        self.assertFalse(r["phase172_prerequisite_checker"]["all_prerequisites_met"])
    def test_execute_gate_blocked_without_flag(self):
        from smr_phase172_core import build_prerequisite_checker, build_execute_apply_gate
        pr = build_prerequisite_checker(None, self.v, self.cg, self.ap)
        r = build_execute_apply_gate(pr, False)
        self.assertFalse(r["phase172_execute_apply_gate"]["can_execute"])
    def test_executor_does_not_apply_without_flag(self):
        from smr_phase172_core import build_prerequisite_checker, build_coverage_state_executor
        pr = build_prerequisite_checker(None, self.v, self.cg, self.ap)
        r = build_coverage_state_executor(pr, False)
        self.assertFalse(r["phase172_coverage_state_executor"]["executed"])
        self.assertEqual(r["phase172_coverage_state_executor"]["candidates_updated"], 0)
    def test_coverage_state_only(self):
        from smr_phase172_core import build_prerequisite_checker, build_coverage_state_executor
        pr = build_prerequisite_checker(None, self.v, self.cg, self.ap)
        r = build_coverage_state_executor(pr, False)
        self.assertTrue(r["phase172_coverage_state_executor"]["coverage_state_only"])
        self.assertTrue(r["phase172_coverage_state_executor"]["trade_state_not_updated"])

class TestPhase172Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase172_core import build_prerequisite_checker, build_coverage_state_executor
        from smr_phase172_guard import build_formal_coverage_apply_guard
        from smr_phase170_validator import validate_owner_input
        from smr_phase171_core import build_apply_confirmation_gate, build_coverage_apply_package
        v = validate_owner_input(None); cg = build_apply_confirmation_gate(v); ap = build_coverage_apply_package(v)
        pr = build_prerequisite_checker(None, v, cg, ap); ex = build_coverage_state_executor(pr, False)
        r = build_formal_coverage_apply_guard(ex)
        self.assertEqual(r["phase172_formal_coverage_apply_guard"]["status"], "pass")
    def test_cc(self):
        from smr_phase172_guard import build_cannot_conclude_guard
        r = build_cannot_conclude_guard()
        self.assertIn("coverage_apply_is_not_trade", r["phase172_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase172Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase172_coverage_apply_board import build
        r = build()
        self.assertEqual(r["phase172_coverage_apply_board"]["guard"], "pass")
    def test_dashboard(self):
        from build_phase172_coverage_apply_dashboard import build_dashboard
        r = build_dashboard()
        self.assertEqual(r["phase172_coverage_apply_dashboard"]["summary"]["guard"], "pass")

class TestPhase172Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase172_coverage_apply_pipeline import run
        r = run("dry-run")
        self.assertEqual(r["phase172_coverage_apply_pipeline"]["guard"], "pass")
    def test_execute_no_apply(self):
        from run_phase172_coverage_apply_pipeline import run
        r = run("execute", False)
        self.assertFalse(r["phase172_coverage_apply_pipeline"]["applied"])
        self.assertTrue(r["phase172_coverage_apply_pipeline"]["coverage_state_only"])

if __name__ == "__main__":
    unittest.main()
