import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase158Config(unittest.TestCase):
    def test_config(self):
        from smr_phase158_config import load_phase158_config
        c = load_phase158_config()
        self.assertEqual(c["phase"], "phase158")
        self.assertTrue(c["static_html_only"])
        self.assertFalse(c["external_js_allowed"])
        self.assertFalse(c["execution_button_enabled"])
        self.assertFalse(c["trade_button_enabled"])
        self.assertFalse(c["form_submit_enabled"])

class TestPhase158UI(unittest.TestCase):
    def test_decision_cards(self):
        from smr_phase158_loaders import load_pending_candidates
        from smr_phase158_ui_data_model import build_decision_ui_data_model
        from smr_phase158_decision_card import build_decision_cards
        candidates = load_pending_candidates()
        model = build_decision_ui_data_model(candidates)
        cards = build_decision_cards(model["phase158_ui_data_model"])
        self.assertEqual(cards["phase158_decision_cards"]["pending_cards"], 8)

    def test_template_renderer_no_auto_approval(self):
        from smr_phase158_loaders import load_pending_candidates
        from smr_phase158_template_renderer import render_decision_template_json
        candidates = load_pending_candidates()
        r = render_decision_template_json(candidates)
        self.assertTrue(r["phase158_template_renderer"]["auto_approval_not_applied"])

    def test_ui_safety_copy(self):
        from smr_phase158_ui_safety_copy import check_ui_safety_copy
        r = check_ui_safety_copy()
        self.assertEqual(r["phase158_ui_safety_copy"]["overall_status"], "pass")

    def test_link_integrity(self):
        from smr_phase158_link_checker import check_ui_links
        r = check_ui_links()
        self.assertEqual(r["phase158_link_checker"]["integrity"], "pass")

class TestPhase158Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase158_decision_ui_pipeline import run
        r = run("dry-run")
        p = r["phase158_decision_ui_pipeline"]
        self.assertEqual(p["decision_cards"], 8)
        self.assertTrue(p["console_page_generated"])
        self.assertEqual(p["link_integrity"], "pass")
        self.assertEqual(p["ui_safety_copy"], "pass")
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["static_html_only"])
        self.assertTrue(p["trade_buttons_disabled"])
        self.assertTrue(p["execution_blocked"])
        self.assertEqual(p["mock_used"], False)

if __name__ == "__main__":
    unittest.main()
