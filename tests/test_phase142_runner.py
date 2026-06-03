import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'jobs'))
from run_phase142_ticker_detail_pipeline import run_pipeline

class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        r = run_pipeline('dry-run')
        p = r['phase142_ticker_detail_pipeline']
        self.assertEqual(p['detail_pages_generated'], 8)
        self.assertEqual(p['quality_gate'], 'pass')
        self.assertEqual(p['violations'], 0)
        self.assertFalse(p['mock_used'])
    def test_safety(self):
        for mode in ['dry-run', 'execute', 'skip-network']:
            r = run_pipeline(mode)
            p = r['phase142_ticker_detail_pipeline']
            self.assertEqual(p['trade_recommendation_created'], 0)
            self.assertEqual(p['paper_order_created'], 0)

if __name__ == '__main__':
    unittest.main()
