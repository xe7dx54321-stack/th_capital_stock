import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase144_feedback_form_builder import build_feedback_forms

class TestFeedbackForms(unittest.TestCase):
    def test_builds(self):
        r = build_feedback_forms()
        self.assertEqual(r['phase144_feedback_forms']['forms'], 5)
        self.assertIn('general_feedback', r['phase144_feedback_forms']['form_types'])
        self.assertIn('source_limitation_confirmation', r['phase144_feedback_forms']['form_types'])

if __name__ == '__main__':
    unittest.main()
