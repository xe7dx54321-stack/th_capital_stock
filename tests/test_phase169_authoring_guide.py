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
        self.assertFalse(c["owner_input_write_allowed"])

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
    def test_example_pack_counts(self):
        from smr_phase169_guide import build_example_pack
        r = build_example_pack()
        self.assertEqual(r["phase169_example_pack"]["valid_example_count"], 5)
        self.assertEqual(r["phase169_example_pack"]["invalid_example_count"], 7)
        self.assertTrue(r["phase169_example_pack"]["valid_examples_exceed_minimum"])
        self.assertTrue(r["phase169_example_pack"]["invalid_examples_exceed_minimum"])
    def test_mixed_all_13_present(self):
        from smr_phase169_guide import build_example_pack
        r = build_example_pack()
        self.assertIn("example_5_mixed_all_13", r["phase169_example_pack"]["valid_examples"])
    def test_unknown_candidate_present(self):
        from smr_phase169_guide import build_example_pack
        r = build_example_pack()
        self.assertIn("invalid_4_unknown_candidate", r["phase169_example_pack"]["invalid_examples"])
    def test_duplicate_present(self):
        from smr_phase169_guide import build_example_pack
        r = build_example_pack()
        self.assertIn("invalid_5_duplicate_candidate", r["phase169_example_pack"]["invalid_examples"])
    def test_bad_option_present(self):
        from smr_phase169_guide import build_example_pack
        r = build_example_pack()
        self.assertIn("invalid_6_bad_option", r["phase169_example_pack"]["invalid_examples"])

class TestPhase169Preflight(unittest.TestCase):
    def test_no_draft(self):
        from smr_phase169_preflight import build_preflight_validator
        r = build_preflight_validator(None)
        self.assertEqual(r["phase169_preflight_validator"]["status"], "no_draft")
    def test_valid_draft(self):
        from smr_phase169_preflight import build_preflight_validator
        draft = {"decisions":[{"candidate_id":tk,"owner_decision":"activate_into_formal_research_coverage","rationale":"Evidence complete.","conditions":["x"],"risk_acknowledgment":"Risk noted."} for tk in ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]]}
        r = build_preflight_validator(draft)
        self.assertEqual(r["phase169_preflight_validator"]["status"], "pass")
    def test_duplicate_detected(self):
        from smr_phase169_preflight import build_preflight_validator
        draft = {"decisions":[{"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage","rationale":"ok","conditions":[],"risk_acknowledgment":"ok"},{"candidate_id":"MRVL","owner_decision":"keep_as_candidate_pending_more_evidence","rationale":"dup","conditions":[],"risk_acknowledgment":"ok"}]}
        r = build_preflight_validator(draft)
        self.assertGreater(r["phase169_preflight_validator"]["violations"], 0)
    def test_unknown_candidate(self):
        from smr_phase169_preflight import build_preflight_validator
        draft = {"decisions":[{"candidate_id":"NVDA","owner_decision":"activate_into_formal_research_coverage","rationale":"ok","conditions":[],"risk_acknowledgment":"ok"}]}
        r = build_preflight_validator(draft)
        self.assertIn("unknown_candidate", str(r["phase169_preflight_validator"]["issues"]))
    def test_missing_rationale(self):
        from smr_phase169_preflight import build_preflight_validator
        draft = {"decisions":[{"candidate_id":"MRVL","owner_decision":"activate_into_formal_research_coverage","rationale":"","conditions":[],"risk_acknowledgment":"ok"}]}
        r = build_preflight_validator(draft)
        self.assertGreater(r["phase169_preflight_validator"]["violations"], 0)
    def test_expectation_matcher(self):
        from smr_phase169_guide import build_example_pack
        from smr_phase169_preflight import build_expectation_matcher
        ep = build_example_pack()
        r = build_expectation_matcher(ep)
        self.assertTrue(r["phase169_expectation_matcher"]["expectations_all_match"])
        self.assertEqual(r["phase169_expectation_matcher"]["examples_checked"], 12)
    def test_sandbox_all_examples(self):
        from smr_phase169_guide import build_example_pack
        from smr_phase169_preflight import build_sandbox_all_examples
        ep = build_example_pack()
        r = build_sandbox_all_examples(ep)
        self.assertTrue(r["phase169_sandbox_all_examples"]["all_examples_checked"])
        self.assertTrue(r["phase169_sandbox_all_examples"]["no_watch_core_update_in_any"])

class TestPhase169Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase169_preflight import build_preflight_validator
        from smr_phase169_guard import build_authoring_guide_guard
        pf = build_preflight_validator()
        r = build_authoring_guide_guard(pf)
        self.assertEqual(r["phase169_authoring_guide_guard"]["status"], "pass")
    def test_quality_gate_enhanced(self):
        from smr_phase169_guide import build_example_pack
        from smr_phase169_preflight import build_expectation_matcher, build_sandbox_all_examples
        from smr_phase169_guard import build_quality_gate
        ep = build_example_pack(); em = build_expectation_matcher(ep); sa = build_sandbox_all_examples(ep)
        r = build_quality_gate(ep, em, sa)
        self.assertEqual(r["phase169_quality_gate"]["status"], "pass")
        self.assertEqual(r["phase169_quality_gate"]["example_coverage_status"], "pass")
    def test_cc_enhanced(self):
        from smr_phase169_guard import build_cannot_conclude_guard
        r = build_cannot_conclude_guard()
        reserved = r["phase169_cannot_conclude_guard"]["reserved_constraints"]
        self.assertIn("valid_example != owner_approval", reserved)
        self.assertIn("reject_example != sell_signal", reserved)
        self.assertIn("activate_example != buy_signal", reserved)

class TestPhase169Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase169_authoring_guide_board import build
        r = build()
        b = r["phase169_authoring_guide_board"]
        self.assertEqual(b["guard"], "pass")
        self.assertEqual(b["valid_examples"], 5)
        self.assertEqual(b["invalid_examples"], 7)
        self.assertTrue(b["expectations_all_match"])
    def test_dashboard(self):
        from build_phase169_authoring_guide_dashboard import build_dashboard
        r = build_dashboard()
        self.assertEqual(r["phase169_authoring_guide_dashboard"]["summary"]["guard"], "pass")

class TestPhase169Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase169_authoring_guide_pipeline import run
        r = run("dry-run")
        p = r["phase169_authoring_guide_pipeline"]
        self.assertEqual(p["guard"], "pass")
        self.assertTrue(p["expectations_all_match"])
    def test_execute(self):
        from run_phase169_authoring_guide_pipeline import run
        self.assertEqual(run("execute")["phase169_authoring_guide_pipeline"]["guard"], "pass")
    def test_skip(self):
        from run_phase169_authoring_guide_pipeline import run
        self.assertEqual(run("skip-network")["phase169_authoring_guide_pipeline"]["guard"], "pass")

if __name__ == "__main__":
    unittest.main()
