import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_gap_risk_html_section import build_gap_risk_html_section

class TestGapRisk(unittest.TestCase):
    def test_builds(self):
        r = build_gap_risk_html_section()
        self.assertIn('phase141_gap_risk_html_section', r)
        self.assertGreater(r['phase141_gap_risk_html_section']['gaps'], 0)
        html = r['phase141_gap_risk_html_section']['html']
        self.assertIn('CNINFO', html)

if __name__ == '__main__':
    unittest.main()
