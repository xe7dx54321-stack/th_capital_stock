import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_evidence_source_limitation_html_section import build_evidence_source_limitation_html_section

class TestEvidenceLimitation(unittest.TestCase):
    def test_builds(self):
        r = build_evidence_source_limitation_html_section()
        self.assertIn('phase141_evidence_source_limitation_html_section', r)
        self.assertGreater(r['phase141_evidence_source_limitation_html_section']['items'], 0)
        html = r['phase141_evidence_source_limitation_html_section']['html']
        self.assertIn('300394', html)
        self.assertIn('688041', html)

if __name__ == '__main__':
    unittest.main()
