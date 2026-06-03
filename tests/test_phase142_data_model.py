import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase142_ticker_detail_data_model import build_ticker_detail_data_model

class TestDataModel(unittest.TestCase):
    def test_builds(self):
        r = build_ticker_detail_data_model()
        self.assertEqual(r['phase142_ticker_detail_data_model']['tickers'], 8)
        self.assertFalse(r['phase142_ticker_detail_data_model']['mock_used'])
    def test_300394(self):
        r = build_ticker_detail_data_model()
        td = r['phase142_ticker_detail_data_model']['ticker_data']
        t394 = [t for t in td if t['ticker'] == '300394.SZ'][0]
        self.assertEqual(t394['thesis_status'], 'unconfirmed')
        self.assertEqual(t394['confidence'], 'low')

if __name__ == '__main__':
    unittest.main()
