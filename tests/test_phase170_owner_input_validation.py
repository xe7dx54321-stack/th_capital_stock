import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase170Config(unittest.TestCase):
    def test_config(self):
        from smr_phase170_config import load_phase170_config
        c = load_phase170_config()
        self.assertEqual(c["phase"], "phase170")
        self.assertTrue(c["schema_validation_enabled"])
        self.assertFalse(c["formal_state_update_allowed"])
        self.assertFalse(c["watch_core_update_allowed"])

class TestPhase170Domain(unittest.TestCase):
    def test_registry(self):
        from smr_phase170_domain_registry import build_phase170_domain_registry
        r = build_phase170_domain_registry()
        self.assertEqual(len(r["phase170_domain_registry"]["domains"]), 4)

class TestPhase170Validator(unittest.TestCase):
    def test_no_input(self):
        from smr_phase170_validator import validate_owner_input
        r = validate_owner_input(None)
        self.assertEqual(r["phase170_schema_validator"]["status"], "no_input")
    def test_valid_input(self):
        from smr_phase170_validator import validate_owner_input
        inp = {"decisions":[{"candidate_id":tk,"owner_decision":"activate_into_formal_research_coverage","rationale":"Evidence complete.","conditions":["x"],"risk_acknowledgment":"Risk noted."} for tk in ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]]}
        r = validate_owner_input(inp)
        self.assertEqual(r["phase170_schema_validator"]["valid_entries"], 13)
        self.assertEqual(r["phase170_schema_validator"]["quarantined_entries"], 0)
    def test_trade_quarantined(self):
        from smr_phase170_validator import validate_owner_input
        inp = {"decisions":[{"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage","rationale":"Buy signal. Target price $250.","conditions":[],"risk_acknowledgment":"ok"}]}
        r = validate_owner_input(inp)
        self.assertGreater(r["phase170_schema_validator"]["quarantined_entries"], 0)
    def test_unknown_candidate_quarantined(self):
        from smr_phase170_validator import validate_owner_input
        inp = {"decisions":[{"candidate_id":"NVDA","owner_decision":"activate_into_formal_research_coverage","rationale":"ok","conditions":[],"risk_acknowledgment":"ok"}]}
        r = validate_owner_input(inp)
        self.assertGreater(r["phase170_schema_validator"]["quarantined_entries"], 0)

class TestPhase170StatePreview(unittest.TestCase):
    def test_state_preview(self):
        from smr_phase170_validator import validate_owner_input
        from smr_phase170_state_preview import build_formal_research_state_preview
        inp = {"decisions":[{"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage","rationale":"ok","conditions":[],"risk_acknowledgment":"ok"}]}
        v = validate_owner_input(inp)
        r = build_formal_research_state_preview(v)
        self.assertTrue(r["phase170_formal_research_state_preview"]["state_not_updated"])
    def test_tier_proposal(self):
        from smr_phase170_validator import validate_owner_input
        from smr_phase170_state_preview import build_tier_proposal_preview
        inp = {"decisions":[{"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage","rationale":"ok","conditions":[],"risk_acknowledgment":"ok"}]}
        v = validate_owner_input(inp)
        r = build_tier_proposal_preview(v)
        self.assertTrue(r["phase170_tier_proposal_preview"]["tier_not_assigned"])

class TestPhase170Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase170_validator import validate_owner_input
        from smr_phase170_guard import build_owner_input_submission_guard
        r = build_owner_input_submission_guard(validate_owner_input(None))
        self.assertEqual(r["phase170_owner_input_submission_guard"]["status"], "pass")
    def test_quality_gate(self):
        from smr_phase170_validator import validate_owner_input
        from smr_phase170_state_preview import build_formal_research_state_preview
        from smr_phase170_guard import build_quality_gate
        v = validate_owner_input(None); s = build_formal_research_state_preview(v)
        r = build_quality_gate(v, s)
        self.assertEqual(r["phase170_quality_gate"]["status"], "fail")
    def test_cc(self):
        from smr_phase170_guard import build_cannot_conclude_guard
        r = build_cannot_conclude_guard()
        self.assertIn("300394 CNINFO org_id missing", r["phase170_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase170Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase170_owner_input_validation_board import build
        r = build()
        self.assertEqual(r["phase170_owner_input_validation_board"]["guard"], "pass")
    def test_dashboard(self):
        from build_phase170_owner_input_validation_dashboard import build_dashboard
        r = build_dashboard()
        self.assertEqual(r["phase170_owner_input_validation_dashboard"]["summary"]["guard"], "pass")

class TestPhase170Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase170_owner_input_validation_pipeline import run
        r = run("dry-run")
        self.assertEqual(r["phase170_owner_input_validation_pipeline"]["guard"], "pass")
    def test_execute(self):
        from run_phase170_owner_input_validation_pipeline import run
        self.assertEqual(run("execute")["phase170_owner_input_validation_pipeline"]["guard"], "pass")
    def test_skip(self):
        from run_phase170_owner_input_validation_pipeline import run
        self.assertEqual(run("skip-network")["phase170_owner_input_validation_pipeline"]["guard"], "pass")

if __name__ == "__main__":
    unittest.main()
