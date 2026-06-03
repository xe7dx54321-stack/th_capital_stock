import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase159Config(unittest.TestCase):
    def test_config(self):
        from smr_phase159_config import load_phase159_config
        c = load_phase159_config()
        self.assertEqual(c["phase"], "phase159")
        self.assertTrue(c["missing_owner_input_allowed"])
        self.assertFalse(c["activation_execution_allowed"])
        self.assertTrue(c["simulation_only"])

class TestPhase159Validators(unittest.TestCase):
    def setUp(self):
        self.candidates = [{"ticker":"MRVL","name":"Marvell","market":"US"},{"ticker":"INTC","name":"Intel","market":"US"}]
        self.allowed = ["approve_research_activation","defer_to_next_review","reject_for_now"]
        self.forbidden = ["buy","sell","target_price"]

    def test_file_locator_no_input(self):
        from smr_phase159_file_locator import locate_owner_input_file
        r = locate_owner_input_file()
        self.assertFalse(r["phase159_file_locator"]["owner_input_present"])

    def test_parser_no_file(self):
        from smr_phase159_file_locator import locate_owner_input_file
        from smr_phase159_json_parser import parse_owner_decision_json
        fl = locate_owner_input_file()
        r = parse_owner_decision_json(fl["phase159_file_locator"])
        self.assertFalse(r["phase159_json_parser"]["parsed_ok"])

    def test_membership_validator(self):
        parsed = {"decisions":[{"ticker":"MRVL","decision":"approve_research_activation"}]}
        from smr_phase159_membership_validator import validate_candidate_membership
        r = validate_candidate_membership(parsed, self.candidates)
        self.assertTrue(r["phase159_membership_validator"]["all_known"])

    def test_forbidden_validator(self):
        parsed = {"decisions":[{"ticker":"MRVL","decision":"approve_research_activation","rationale":"Good theme fit for AI research coverage."}]}
        from smr_phase159_forbidden_validator import validate_no_forbidden_terms
        r = validate_no_forbidden_terms(parsed, self.forbidden)
        self.assertTrue(r["phase159_forbidden_validator"]["all_clean"])

    def test_forbidden_catches_buy(self):
        parsed = {"decisions":[{"ticker":"MRVL","decision":"approve_research_activation","rationale":"buy this stock now."}]}
        from smr_phase159_forbidden_validator import validate_no_forbidden_terms
        r = validate_no_forbidden_terms(parsed, self.forbidden)
        self.assertFalse(r["phase159_forbidden_validator"]["all_clean"])

class TestPhase159Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase159_submission_pipeline import run
        r = run("dry-run")
        p = r["phase159_submission_pipeline"]
        self.assertFalse(p["owner_input_present"])
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["submission_not_execution"])
        self.assertTrue(p["validation_not_activation"])
        self.assertTrue(p["preview_not_real"])
        self.assertTrue(p["manifest_not_watch_update"])
        self.assertEqual(p["mock_used"], False)

if __name__ == "__main__":
    unittest.main()
