import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'reporting'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'jobs'))
from run_phase141_html_dashboard_pipeline import run_pipeline

class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        r = run_pipeline('dry-run')
        p = r['phase141_html_dashboard_pipeline']
        self.assertEqual(p['mode'], 'dry-run')
        self.assertEqual(p['quality_gate'], 'pass')
        self.assertEqual(p['cannot_conclude_guard'], 'pass')
        self.assertEqual(p['violations'], 0)
        self.assertFalse(p['html_saved'])
        self.assertTrue(p['static_html_only'])
        self.assertFalse(p['mock_used'])
        self.assertEqual(p['pending_created'], 0)

    def test_execute(self):
        r = run_pipeline('execute')
        p = r['phase141_html_dashboard_pipeline']
        self.assertEqual(p['mode'], 'execute')
        self.assertEqual(p['quality_gate'], 'pass')
        self.assertTrue(p['html_saved'])
        self.assertTrue(p['output_path_ignored'])

    def test_skip_network(self):
        r = run_pipeline('skip-network')
        p = r['phase141_html_dashboard_pipeline']
        self.assertEqual(p['mode'], 'skip-network')
        self.assertEqual(p['quality_gate'], 'pass')

    def test_safety_all_modes(self):
        for mode in ['dry-run', 'execute', 'skip-network']:
            r = run_pipeline(mode)
            p = r['phase141_html_dashboard_pipeline']
            self.assertFalse(p['mock_used'], f'mock_used in {mode}')
            self.assertFalse(p['fixture_used'], f'fixture_used in {mode}')
            self.assertEqual(p['pending_created'], 0)
            self.assertEqual(p['paper_order_created'], 0)
            self.assertEqual(p['real_trade_created'], 0)
            self.assertEqual(p['target_price_output'], 0)
            self.assertEqual(p['position_sizing_output'], 0)

if __name__ == '__main__':
    unittest.main()
