import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_css_style_builder import build_css_style

class TestCSSBuilder(unittest.TestCase):
    def test_css_builds(self):
        r = build_css_style()
        self.assertIn('phase141_css_style_builder', r)
        self.assertTrue(r['phase141_css_style_builder']['ready'])
        css = r['phase141_css_style_builder']['css']
        self.assertIn(':root', css)
        self.assertIn('--bg', css)
        self.assertIn('--card', css)
        self.assertIn('ticker-card', css)

    def test_no_external_refs(self):
        r = build_css_style()
        css = r['phase141_css_style_builder']['css']
        self.assertNotIn('@import url', css)
        self.assertNotIn('cdn.', css.lower())

if __name__ == '__main__':
    unittest.main()
