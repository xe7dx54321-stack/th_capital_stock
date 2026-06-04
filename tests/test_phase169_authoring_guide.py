import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase169Config(unittest.TestCase):
    def test_config(self):
        from smr_phase169_config import load_phase169_config
        c = load_phase169_config()
        self.assertEqual(c["phase"], "phase169")
        self.assertTrue(c["authoring_guide_enabled"])
        self.assertTrue(c["example_pack_enabled"])
        self.assertFalse(c["owner_input_write_allowed"])
        self.assertFalse(c["real_decision_submission_allowed"])

class TestPhase169Domain(unittest.TestCase):
    def test_registry(self):
        from smr_phase169_domain_registry import build_phase169_domain_registry
        r = build_phase169_domain_registry()
        self.assertEqual(len(r["phase169_domain_registry"]["domains"]), 4)

class TestPhase169Guide(unittest.TestCase):
    def test_fill_guide(self):
        from smr_phase169_guide import build_fill_guide
        r = build_fill_guide()
        self.assertEqual(len(r["phase169_fill_guide"]["fields"]), 5)
        self.assertEqual(len(r["phase169_fill_guide"]["rules"]), 6)
    def test_example_pack(self):
        from smr_phase169_guide import build_example_pack
        r = build_example_pack()
        self.assertEqual(r["phase169_example_pack"]["valid_example_count"], 4)
        self.assertEqual(r["phase169_example_pack"]["invalid_example_count"], 3)

class TestPhase169Preflight(unittest.TestCase):
    def test_no_draft(self):
        from smr_phase169_preflight import build_preflight_validator
        r = build_preflight_validator(None)
        self.assertEqual(r["phase169_preflight_validator"]["status"], "no_draft")
    def test_valid_draft(self):
        from smr_phase169_preflight import build_preflight_validator
        draft = {"decisions":[{"candidate_id":tk,"owner_decision":"activate_into_formal_research_coverage","rationale":"Evidence complete, agent passed.","conditions":["tier_assignment"],"risk_acknowledgment":"Standard risk noted."} for tk in ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]]}
        r = build_preflight_validator(draft)
        self.assertEqual(r["phase169_preflight_validator"]["status"], "pass")
    def test_trade_terms_blocked(self):
        from smr_phase169_preflight import build_preflight_validator
        draft = {"decisions":[{"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage","rationale":"Target price $250. Buy signal.","conditions":[],"risk_acknowledgment":"ok"}]}
        r = build_preflight_validator(draft)
        self.assertGreater(r["phase169_preflight_validator"]["violations"], 0)
    def test_sandbox(self):
        from smr_phase169_preflight import build_sandbox_simulation
        draft = {"decisions":[{"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage","rationale":"ok","conditions":[],"risk_acknowledgment":"ok"},{"candidate_id":"AMAT","owner_decision":"keep_as_candidate_pending_more_evidence","rationale":"ok","conditions":[],"risk_acknowledgment":"ok"}]}
        r = build_sandbox_simulation(draft)
        self.assertTrue(r["phase169_sandbox_simulation"]["sandbox_not_real_execution"])
        self.assertFalse(r["phase169_sandbox_simulation"]["watch_core_would_update"])

class TestPhase169Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase169_preflight import build_preflight_validator
        from smr_phase169_guard import build_authoring_guide_guard
        pf = build_preflight_validator()
        r = build_authoring_guide_guard(pf)
        self.assertEqual(r["phase169_authoring_guide_guard"]["status"], "pass")
    def test_quality_gate(self):
        from smr_phase169_guard import build_quality_gate
        r = build_quality_gate()
        self.assertEqual(r["phase169_quality_gate"]["status"], "pass")
    def test_cc(self):
        from smr_phase169_guard import build_cannot_conclude_guard
        r = build_cannot_conclude_guard()
        self.assertIn("300394 CNINFO org_id missing", r["phase169_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase169Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase169_authoring_guide_board import build
        r = build()
        self.assertEqual(r["phase169_authoring_guide_board"]["guard"], "pass")
    def test_dashboard(self):
        from build_phase169_authoring_guide_dashboard import build_dashboard
        r = build_dashboard()
        self.assertEqual(r["phase169_authoring_guide_dashboard"]["summary"]["guard"], "pass")

class TestPhase169Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase169_authoring_guide_pipeline import run
        r = run("dry-run")
        self.assertEqual(r["phase169_authoring_guide_pipeline"]["guard"], "pass")
        self.assertTrue(r["phase169_authoring_guide_pipeline"]["guide_not_auto_write"])
    def test_execute(self):
        from run_phase169_authoring_guide_pipeline import run
        self.assertEqual(run("execute")["phase169_authoring_guide_pipeline"]["guard"], "pass")
    def test_skip(self):
        from run_phase169_authoring_guide_pipeline import run
        self.assertEqual(run("skip-network")["phase169_authoring_guide_pipeline"]["guard"], "pass")

if __name__ == "__main__":
    unittest.main()
