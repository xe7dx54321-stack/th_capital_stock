import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_dashboard_data_model import build_dashboard_data_model

class TestDashboardDataModel(unittest.TestCase):
    def test_model_builds(self):
        result = build_dashboard_data_model()
        self.assertIn('phase141_dashboard_data_model', result)
        model = result['phase141_dashboard_data_model']['model']
        self.assertEqual(len(model['tickers']), 8)
        self.assertEqual(model['system_status']['operational_score'], 100)
        self.assertTrue(model['system_status']['research_only'])

    def test_all_tickers_present(self):
        result = build_dashboard_data_model()
        tickers = [t['ticker'] for t in result['phase141_dashboard_data_model']['model']['tickers']]
        for t in ['NVDA', 'AVGO', '688041.SH', '09988.HK', '00700.HK', '300308.SZ', '002230.SZ', '300394.SZ']:
            self.assertIn(t, tickers)

    def test_300394_is_unconfirmed(self):
        result = build_dashboard_data_model()
        t394 = [t for t in result['phase141_dashboard_data_model']['model']['tickers'] if t['ticker'] == '300394.SZ'][0]
        self.assertEqual(t394['status'], 'unconfirmed')
        self.assertEqual(t394['confidence'], 'low')

    def test_no_mock_fixture(self):
        result = build_dashboard_data_model()
        self.assertFalse(result['phase141_dashboard_data_model']['mock_used'])
        self.assertFalse(result['phase141_dashboard_data_model']['fixture_used'])

if __name__ == '__main__':
    unittest.main()
