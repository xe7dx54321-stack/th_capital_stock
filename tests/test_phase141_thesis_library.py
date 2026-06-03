import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_thesis_library_html_section import build_thesis_library_html_section

class TestThesisLibrary(unittest.TestCase):
    def test_builds(self):
        r = build_thesis_library_html_section()
        self.assertIn('phase141_thesis_library_html_section', r)
        self.assertGreater(r['phase141_thesis_library_html_section']['theses'], 0)
        self.assertTrue(r['phase141_thesis_library_html_section']['not_trade'])

if __name__ == '__main__':
    unittest.main()
