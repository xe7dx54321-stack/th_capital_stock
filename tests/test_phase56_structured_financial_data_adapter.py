import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Phase56AdapterTests(unittest.TestCase):
    def test_dry_run_returns_zero_records(self):
        from smr_structured_financial_data_adapter import fetch_structured_financial_data
        r = fetch_structured_financial_data(mode='dry-run')
        df = r['structured_financial_data_fetch']
        self.assertEqual(df['records_loaded'], 0)
    def test_skip_network_returns_unavailable(self):
        from smr_structured_financial_data_adapter import fetch_structured_financial_data
        r = fetch_structured_financial_data(mode='skip-network')
        df = r['structured_financial_data_fetch']
        self.assertFalse(df['real_data_available'])
    def test_period_conversion(self):
        from smr_structured_financial_data_adapter import _period_to_quarters
        self.assertEqual(_period_to_quarters('20251231'), '2025Q4')
        self.assertEqual(_period_to_quarters('20260331'), '2026Q1')

if __name__ == '__main__':
    unittest.main()
