import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_static_html_layout_builder import build_static_html_layout

class TestHTMLLayout(unittest.TestCase):
    def test_layout_builds(self):
        r = build_static_html_layout()
        self.assertIn('phase141_static_html_layout_builder', r)
        self.assertTrue(r['phase141_static_html_layout_builder']['ready'])
        layout = r['phase141_static_html_layout_builder']['layout']
        self.assertIn('<!DOCTYPE html>', layout)
        self.assertIn('TH Capital Research Console', layout)
        self.assertIn('ticker-cards', layout)
        self.assertIn('thesis-library', layout)
        self.assertIn('No trade recommendations', layout)

    def test_sections_present(self):
        r = build_static_html_layout()
        layout = r['phase141_static_html_layout_builder']['layout']
        for s in ['ticker-cards','thesis-library','evidence-sources','daily-delivery','owner-actions','gap-risk','feedback-template','artifact-links']:
            self.assertIn(s, layout)

if __name__ == '__main__':
    unittest.main()
