import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_feedback_template_html_section import build_feedback_template_html_section

class TestFeedbackTemplate(unittest.TestCase):
    def test_builds(self):
        r = build_feedback_template_html_section()
        self.assertIn('phase141_feedback_template_html_section', r)
        self.assertEqual(r['phase141_feedback_template_html_section']['templates'], 4)
        html = r['phase141_feedback_template_html_section']['html']
        self.assertIn('Deep Dive Request', html)
        self.assertIn('Evidence Challenge', html)

if __name__ == '__main__':
    unittest.main()
