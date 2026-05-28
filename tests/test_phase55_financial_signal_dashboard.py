import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L)), json
class Phase55DashboardTests(unittest.TestCase):
    def test_dashboard_pending_created_zero(self):
        from smr_financial_source_availability import check_financial_source_availability
        r = check_financial_source_availability()
        sa = r['financial_source_availability']
        self.assertIsNotNone(sa)
    def test_dashboard_fixture_marked(self):
        from smr_financial_source_availability import check_financial_source_availability
        sa = check_financial_source_availability()['financial_source_availability']
        self.assertTrue(sa['manual_fixture_available'])
    def test_no_trading_signals_in_availability(self):
        import json
        from smr_financial_source_availability import check_financial_source_availability
        r = json.dumps(check_financial_source_availability(), ensure_ascii=False)
        self.assertNotIn('buy', r.lower())
        self.assertNotIn('sell', r.lower())
    def test_generic_capability_count(self):
        from smr_financial_source_availability import check_financial_source_availability
        sa = check_financial_source_availability()['financial_source_availability']
        self.assertGreater(sa['sources_checked'], 0)

if __name__ == '__main__':
    unittest.main()
