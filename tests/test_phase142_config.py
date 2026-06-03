import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase142_config import load_phase142_config

class TestPhase142Config(unittest.TestCase):
    def test_loads(self):
        cfg = load_phase142_config()
        self.assertEqual(cfg['phase'], 'phase142')
        self.assertTrue(cfg['research_only'])
        self.assertTrue(cfg['static_html_only'])
        self.assertFalse(cfg['external_js_allowed'])
        self.assertFalse(cfg['safety']['trade_recommendation_allowed'])

if __name__ == '__main__':
    unittest.main()
