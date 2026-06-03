import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_html_quality_gate import run_html_quality_gate

class TestQualityGate(unittest.TestCase):
    def setUp(self):
        self.valid_html = '<!DOCTYPE html><html><head><meta charset=UTF-8><title>Test</title></head><body><section id=ticker-cards></section><section id=thesis-library></section><section id=evidence-sources></section><section id=daily-delivery></section><section id=owner-actions></section><section id=gap-risk></section><section id=feedback-template></section><section id=artifact-links></section><nav class=nav-bar></nav><div class=status-bar></div><footer>Research-only console</footer></body></html>'

    def test_valid_html_passes(self):
        r = run_html_quality_gate(self.valid_html)
        self.assertEqual(r['phase141_html_quality_gate']['overall_status'], 'pass')
        self.assertTrue(r['phase141_html_quality_gate']['all_pass'])

    def test_missing_doctype_fails(self):
        html = '<html><head></head><body></body></html>'
        r = run_html_quality_gate(html)
        self.assertIn('has_doctype', r['phase141_html_quality_gate']['failed_checks'])

    def test_cdn_rejected(self):
        html = self.valid_html + '<link href=https://cdn.example.com/style.css>'
        r = run_html_quality_gate(html)
        self.assertIn('no_cdn_link', r['phase141_html_quality_gate']['failed_checks'])

if __name__ == '__main__':
    unittest.main()
