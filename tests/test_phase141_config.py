import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_config import load_config

class TestPhase141Config(unittest.TestCase):
    def test_config_loads(self):
        cfg = load_config()
        self.assertEqual(cfg['phase'], 'phase141')
        self.assertTrue(cfg['research_only'])
        self.assertTrue(cfg['static_html_only'])
        self.assertTrue(cfg['no_external_js'])
        self.assertTrue(cfg['no_cdn'])
        self.assertTrue(cfg['no_local_server'])
        self.assertEqual(len(cfg['target_tickers']), 8)
        self.assertIn('NVDA', cfg['target_tickers'])
        self.assertIn('300394.SZ', cfg['target_tickers'])

    def test_safety_boundary(self):
        cfg = load_config()
        s = cfg['safety']
        self.assertFalse(s['mock'])
        self.assertFalse(s['fixture'])
        self.assertFalse(s['raw'])
        self.assertFalse(s['ocr'])
        self.assertFalse(s['browser'])
        self.assertEqual(s['paper_order'], 0)
        self.assertEqual(s['paper_trade'], 0)
        self.assertEqual(s['target_price'], 0)
        self.assertEqual(s['position_sizing'], 0)
        self.assertFalse(s['trade_recommendation_allowed'])
        self.assertFalse(s['target_price_output_allowed'])
        self.assertFalse(s['position_sizing_allowed'])

if __name__ == '__main__':
    unittest.main()
