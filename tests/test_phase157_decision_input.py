import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase157Config(unittest.TestCase):
    def test_config(self):
        from smr_phase157_config import load_phase157_config
        c = load_phase157_config()
        self.assertEqual(c["phase"], "phase157")
        self.assertTrue(c["research_only"])
        self.assertTrue(c["simulation_only"])
        self.assertFalse(c["activation_execution_allowed"])
        self.assertFalse(c["tier_update_execution_allowed"])
        self.assertTrue(c["allow_missing_owner_input"])

class TestPhase157Workflow(unittest.TestCase):
    def setUp(self):
        self.candidates = [{"ticker":"MRVL","name":"Marvell","market":"US"},{"ticker":"INTC","name":"Intel","market":"US"}]

    def test_template_export(self):
        from smr_phase157_template_exporter import export_decision_template
        r = export_decision_template(self.candidates)
        self.assertTrue(r["phase157_template_exporter"]["template_exported"])
        self.assertEqual(r["phase157_template_exporter"]["candidates"], 2)

    def test_import_no_input(self):
        from smr_phase157_template_importer import import_decision_template
        r = import_decision_template(None, self.candidates)
        self.assertFalse(r["phase157_template_importer"]["owner_input_present"])
        self.assertTrue(r["phase157_template_importer"]["all_pending"])
        self.assertEqual(r["phase157_template_importer"]["decisions_imported"], 2)

    def test_summary_no_input_all_pending(self):
        from smr_phase157_template_exporter import export_decision_template
        from smr_phase157_template_importer import import_decision_template
        from smr_phase157_decision_parser import parse_owner_decisions
        from smr_phase157_decision_summary import classify_owner_decision_summary
        exported = export_decision_template(self.candidates)
        imported = import_decision_template(None, self.candidates)
        parsed = parse_owner_decisions(imported["phase157_template_importer"])
        summary = classify_owner_decision_summary(parsed["phase157_decision_parser"],imported["phase157_template_importer"])
        s = summary["phase157_decision_summary"]
        self.assertFalse(s["owner_input_present"])
        self.assertEqual(s["summary"]["pending"], 2)
        self.assertEqual(s["summary"]["approved"], 0)

    def test_simulation_not_execution(self):
        from smr_phase157_approved_simulator import simulate_approved_activation
        r = simulate_approved_activation([])
        self.assertTrue(r["phase157_approved_simulator"]["simulation_only"])

    def test_execution_blocked(self):
        from smr_phase157_dependency_checker import check_activation_dependencies
        r = check_activation_dependencies({"execution_plans":[]})
        self.assertTrue(r["phase157_dependency_checker"]["execution_blocked"])

class TestPhase157Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase157_decision_input_pipeline import run
        r = run("dry-run")
        p = r["phase157_decision_input_pipeline"]
        self.assertFalse(p["owner_input_present"])
        self.assertEqual(p["pending"], 8)
        self.assertEqual(p["approved"], 0)
        self.assertTrue(p["simulation_only"])
        self.assertTrue(p["execution_blocked"])
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["approve_not_buy"])
        self.assertTrue(p["reject_not_sell"])
        self.assertEqual(p["mock_used"], False)

if __name__ == "__main__":
    unittest.main()
