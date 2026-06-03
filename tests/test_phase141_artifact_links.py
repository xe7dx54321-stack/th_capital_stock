import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_artifact_link_html_section import build_artifact_link_html_section

class TestArtifactLinks(unittest.TestCase):
    def test_builds(self):
        r = build_artifact_link_html_section()
        self.assertIn('phase141_artifact_link_html_section', r)
        self.assertGreater(r['phase141_artifact_link_html_section']['links'], 0)

if __name__ == '__main__':
    unittest.main()
