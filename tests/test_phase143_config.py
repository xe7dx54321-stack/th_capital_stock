import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase143_config import load_phase143_config

class TestPhase143Config(unittest.TestCase):
    def test_loads(self):
        cfg = load_phase143_config()
        self.assertTrue(cfg['research_only'])
        self.assertTrue(cfg['cross_link_enabled'])
        self.assertFalse(cfg['external_js_allowed'])

if __name__ == '__main__':
    unittest.main()
