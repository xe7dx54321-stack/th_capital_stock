import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Phase56SigTests(unittest.TestCase):
    def test_signals_has_real_data_flag(self):
        from smr_real_financial_phase55_integration import integrate_real_with_phase55
        r = integrate_real_with_phase55()
        di = r['real_financial_phase55_integration']
        self.assertIn('real_records_available', di)
    def test_fixture_not_used_in_signals(self):
        from smr_real_financial_phase55_integration import integrate_real_with_phase55
        r = integrate_real_with_phase55()
        di = r['real_financial_phase55_integration']
        if di['real_records_available'] > 0:
            self.assertTrue(di['signals_recalculated_with_real_data'])

if __name__ == '__main__':
    unittest.main()
