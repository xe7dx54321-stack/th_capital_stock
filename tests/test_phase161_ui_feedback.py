import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase161Config(unittest.TestCase):
    def test_config(self):
        from smr_phase161_config import load_phase161_config
        c = load_phase161_config()
        self.assertEqual(c["phase"], "phase161")
        self.assertTrue(c["research_only"])
        self.assertTrue(c["submission_ui_feedback_enabled"])
        self.assertTrue(c["static_html_only"])
        self.assertFalse(c["external_js_allowed"])
        self.assertFalse(c["execution_button_enabled"])
        self.assertFalse(c["trade_button_enabled"])
        self.assertFalse(c["form_submit_enabled"])
        self.assertFalse(c["activation_execution_allowed"])

class TestPhase161DomainRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase161_domain_registry import build_phase161_domain_registry
        r = build_phase161_domain_registry()
        dr = r["phase161_domain_registry"]
        self.assertEqual(len(dr["domains"]), 3)
        self.assertFalse(dr["mock_used"])

class TestPhase161Loaders(unittest.TestCase):
    def test_loaders(self):
        from smr_phase161_loaders import (load_phase160_context, load_phase159_context,
                                           load_phase158_context, load_phase156_context, load_phase153_context)
        for fn in [load_phase160_context, load_phase159_context, load_phase158_context,
                    load_phase156_context, load_phase153_context]:
            r = fn()
            self.assertFalse(list(r.values())[0]["mock_used"])
            self.assertFalse(list(r.values())[0]["fixture_used"])

class TestPhase161UIModel(unittest.TestCase):
    def test_model(self):
        from smr_phase161_ui_data_model import build_example_pack_ui_model
        m = build_example_pack_ui_model()
        d = m["phase161_ui_data_model"]
        lib = d["example_library"]
        self.assertEqual(lib["total"], 10)
        self.assertEqual(lib["valid_count"], 5)
        self.assertEqual(lib["invalid_count"], 5)
        self.assertEqual(d["sandbox_summary"]["total_execution"], 0)
        self.assertFalse(d["phase159_status"]["owner_input_present"])

class TestPhase161Panels(unittest.TestCase):
    def setUp(self):
        from smr_phase161_ui_data_model import build_example_pack_ui_model
        self.model = build_example_pack_ui_model()

    def test_example_library_panel(self):
        from smr_phase161_panels import build_example_library_panel
        r = build_example_library_panel(self.model)
        p = r["phase161_example_library_panel"]
        self.assertEqual(p["valid_cards"], 5)
        self.assertEqual(p["invalid_cards"], 5)
        self.assertIn("example-library-panel", p["panel_html"])

    def test_sandbox_result_panel(self):
        from smr_phase161_panels import build_sandbox_result_panel
        r = build_sandbox_result_panel(self.model)
        p = r["phase161_sandbox_result_panel"]
        self.assertIn("sandbox-result-panel", p["panel_html"])

    def test_quarantine_panel(self):
        from smr_phase161_panels import build_quarantine_explanation_panel
        r = build_quarantine_explanation_panel()
        p = r["phase161_quarantine_explanation_panel"]
        self.assertIn("quarantine-explanation-panel", p["panel_html"])
        self.assertIn("NOT an investment opinion", p["panel_html"])

    def test_safe_manifest_panel(self):
        from smr_phase161_panels import build_safe_manifest_explanation_panel
        r = build_safe_manifest_explanation_panel()
        p = r["phase161_safe_manifest_explanation_panel"]
        self.assertIn("safe-manifest-explanation-panel", p["panel_html"])

    def test_phase159_feedback_panel(self):
        from smr_phase161_panels import build_phase159_feedback_panel
        r = build_phase159_feedback_panel(self.model)
        p = r["phase161_phase159_feedback_panel"]
        self.assertIn("phase159-feedback-panel", p["panel_html"])

    def test_workflow_panel(self):
        from smr_phase161_panels import build_workflow_instruction_panel
        r = build_workflow_instruction_panel()
        p = r["phase161_workflow_instruction_panel"]
        self.assertIn("workflow-instruction-panel", p["panel_html"])
        self.assertIn("owner_decision_input.json", p["panel_html"])

    def test_command_panel(self):
        from smr_phase161_panels import build_next_command_panel
        r = build_next_command_panel()
        p = r["phase161_next_command_panel"]
        self.assertIn("next-command-panel", p["panel_html"])

class TestPhase161Console(unittest.TestCase):
    def test_console_page(self):
        from smr_phase161_console import build_console_page_html
        r = build_console_page_html()
        p = r["phase161_console_page"]
        self.assertTrue(p["page_generated"])
        self.assertTrue(p["static_html"])
        self.assertFalse(p["external_js"])
        self.assertIn("console-container", p["page_html"])

    def test_nav_integration(self):
        from smr_phase161_console import build_nav_integration
        r = build_nav_integration()
        n = r["phase161_nav_integration"]
        self.assertTrue(n["integrated"])
        self.assertEqual(len(n["nav_items"]), 7)

    def test_css_extension(self):
        from smr_phase161_console import build_css_extension
        r = build_css_extension()
        c = r["phase161_css_extension"]
        self.assertTrue(c["static_only"])
        self.assertTrue(len(c["css"]) > 100)

class TestPhase161Safety(unittest.TestCase):
    def test_ui_safety_copy(self):
        from smr_phase161_panels import build_ui_safety_copy
        r = build_ui_safety_copy()
        s = r["phase161_ui_safety_copy"]
        self.assertEqual(s["overall_status"], "pass")
        self.assertEqual(s["violations"], 0)

    def test_link_integrity(self):
        from smr_phase161_panels import build_link_integrity
        r = build_link_integrity()
        l = r["phase161_link_integrity"]
        self.assertEqual(l["overall_status"], "pass")
        self.assertEqual(l["broken_links"], 0)

class TestPhase161Guard(unittest.TestCase):
    def test_guard_pass(self):
        from smr_phase161_guard import build_ui_feedback_guard
        g = build_ui_feedback_guard()
        self.assertEqual(g["phase161_ui_feedback_guard"]["status"], "pass")
        self.assertEqual(g["phase161_ui_feedback_guard"]["violations"], 0)

class TestPhase161QualityGate(unittest.TestCase):
    def test_quality_pass(self):
        from smr_phase161_quality_gate import build_quality_gate
        q = build_quality_gate()
        self.assertEqual(q["phase161_quality_gate"]["status"], "pass")

class TestPhase161CannotConclude(unittest.TestCase):
    def test_cc_pass(self):
        from smr_phase161_cannot_conclude_guard import build_cannot_conclude_guard
        cc = build_cannot_conclude_guard()
        self.assertEqual(cc["phase161_cannot_conclude_guard"]["status"], "pass")

class TestPhase161Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase161_ui_feedback_pipeline import run
        r = run("dry-run")
        p = r["phase161_ui_feedback_pipeline"]
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["cannot_conclude_guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertEqual(p["sandbox_execution"], 0)
        self.assertTrue(p["ui_feedback_not_execution"])
        self.assertTrue(p["static_html_only"])
        self.assertFalse(p["execution_button_enabled"])
        self.assertFalse(p["trade_button_enabled"])
        self.assertEqual(p["mock_used"], False)
        self.assertEqual(p["pending_created"], 0)

    def test_execute(self):
        from run_phase161_ui_feedback_pipeline import run
        r = run("execute")
        p = r["phase161_ui_feedback_pipeline"]
        self.assertEqual(p["guard"], "pass")
        self.assertTrue(p["console_html_saved"])

    def test_skip_network(self):
        from run_phase161_ui_feedback_pipeline import run
        r = run("skip-network")
        p = r["phase161_ui_feedback_pipeline"]
        self.assertEqual(p["guard"], "pass")

if __name__ == "__main__":
    unittest.main()
