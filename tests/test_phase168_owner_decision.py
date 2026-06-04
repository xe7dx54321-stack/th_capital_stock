import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase168Config(unittest.TestCase):
    def test_config(self):
        from smr_phase168_config import load_phase168_config
        c = load_phase168_config()
        self.assertEqual(c["phase"], "phase168")
        self.assertTrue(c["research_only"])
        self.assertTrue(c["activation_simulation_only"])
        self.assertFalse(c["real_activation_execution_allowed"])
        self.assertFalse(c["watch_core_update_allowed"])
        self.assertFalse(c["target_price_output_allowed"])

class TestPhase168Domain(unittest.TestCase):
    def test_registry(self):
        from smr_phase168_domain_registry import build_phase168_domain_registry
        r = build_phase168_domain_registry()
        self.assertEqual(len(r["phase168_domain_registry"]["domains"]), 3)

class TestPhase168Loaders(unittest.TestCase):
    def test_load_phase167(self):
        from smr_phase168_loaders import load_phase167_context
        r = load_phase167_context()
        self.assertEqual(r["phase167_context"]["drafts"], 13)
    def test_load_phase159(self):
        from smr_phase168_loaders import load_phase159_decision_template
        r = load_phase159_decision_template()
        self.assertTrue(r["phase159_decision_template"]["auto_submit_disabled"])

class TestPhase168Validator(unittest.TestCase):
    def test_no_input(self):
        from smr_phase168_validator import build_owner_decision_input_validator
        r = build_owner_decision_input_validator(None)
        self.assertEqual(r["phase168_owner_decision_input_validator"]["status"], "no_input_submitted")
    def test_valid_input(self):
        from smr_phase168_validator import build_owner_decision_input_validator
        inp = {"decisions":[{"candidate_id":tk,"owner_decision":"activate_into_formal_research_coverage"} for tk in ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]]}
        r = build_owner_decision_input_validator(inp)
        self.assertEqual(r["phase168_owner_decision_input_validator"]["status"], "pass")
    def test_trade_blocked(self):
        from smr_phase168_validator import build_owner_decision_input_validator
        inp = {"decisions":[{"candidate_id":"MRVL","owner_decision":"buy"}]}
        r = build_owner_decision_input_validator(inp)
        self.assertFalse(r["phase168_owner_decision_input_validator"]["checks"]["no_trade_language"])

class TestPhase168Diff(unittest.TestCase):
    def test_diff_no_input(self):
        from smr_phase168_diff import build_owner_decision_diff_engine
        r = build_owner_decision_diff_engine(None)
        self.assertEqual(len(r["phase168_owner_decision_diff_engine"]["diffs"]), 13)
    def test_diff_with_input(self):
        from smr_phase168_diff import build_owner_decision_diff_engine
        inp = {"decisions":[{"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage"}]}
        r = build_owner_decision_diff_engine(inp)
        self.assertTrue(r["phase168_owner_decision_diff_engine"]["diff_not_auto_execution"])

class TestPhase168Activation(unittest.TestCase):
    def test_simulator_no_input(self):
        from smr_phase168_activation import build_activation_simulator
        r = build_activation_simulator(None)
        s = r["phase168_activation_simulator"]
        self.assertEqual(s["candidates"], 13)
        self.assertTrue(s["simulation_only"])
        self.assertFalse(s["real_activation_executed"])
        self.assertFalse(s["watch_core_updated"])
    def test_simulator_with_activation(self):
        from smr_phase168_activation import build_activation_simulator, build_coverage_proposal_builder
        inp = {"decisions":[{"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage"},{"candidate_id":"AMAT","owner_decision":"keep_as_candidate_pending_more_evidence"}]}
        s = build_activation_simulator(inp)
        p = build_coverage_proposal_builder(s)
        self.assertEqual(s["phase168_activation_simulator"]["activated_count"], 1)
        self.assertTrue(p["phase168_coverage_proposal_builder"]["coverage_proposal_not_portfolio_action"])

class TestPhase168Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase168_validator import build_owner_decision_input_validator
        from smr_phase168_activation import build_activation_simulator
        from smr_phase168_guard import build_owner_decision_submission_guard
        v = build_owner_decision_input_validator(None)
        s = build_activation_simulator(None)
        r = build_owner_decision_submission_guard(v, s)
        self.assertEqual(r["phase168_owner_decision_submission_guard"]["status"], "pass")
    def test_quality_gate(self):
        from smr_phase168_activation import build_activation_simulator
        from smr_phase168_diff import build_owner_decision_diff_engine
        from smr_phase168_guard import build_quality_gate
        s = build_activation_simulator(None)
        d = build_owner_decision_diff_engine(None)
        r = build_quality_gate(s, d)
        self.assertEqual(r["phase168_quality_gate"]["status"], "pass")
    def test_cc(self):
        from smr_phase168_guard import build_cannot_conclude_guard
        r = build_cannot_conclude_guard()
        self.assertIn("300394 CNINFO org_id missing", r["phase168_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase168Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase168_owner_decision_board import build
        r = build()
        self.assertEqual(r["phase168_owner_decision_board"]["guard"], "pass")
    def test_dashboard(self):
        from build_phase168_owner_decision_dashboard import build_dashboard
        r = build_dashboard()
        self.assertEqual(r["phase168_owner_decision_dashboard"]["summary"]["guard"], "pass")

class TestPhase168Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase168_owner_decision_pipeline import run
        r = run("dry-run")
        p = r["phase168_owner_decision_pipeline"]
        self.assertEqual(p["guard"], "pass")
        self.assertTrue(p["simulation_only"])
    def test_execute(self):
        from run_phase168_owner_decision_pipeline import run
        r = run("execute")
        self.assertEqual(r["phase168_owner_decision_pipeline"]["guard"], "pass")
    def test_skip(self):
        from run_phase168_owner_decision_pipeline import run
        r = run("skip-network")
        self.assertEqual(r["phase168_owner_decision_pipeline"]["guard"], "pass")

if __name__ == "__main__":
    unittest.main()
