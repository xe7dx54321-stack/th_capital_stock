import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Phase56IntTests(unittest.TestCase):
    def test_integration_has_real_records_flag(self):
        from smr_real_financial_phase55_integration import integrate_real_with_phase55
        r = integrate_real_with_phase55()
        di = r['real_financial_phase55_integration']
        self.assertIn('real_records_available', di)
    def test_integration_never_overrides_real_with_fixture(self):
        from smr_real_financial_phase55_integration import integrate_real_with_phase55
        r = integrate_real_with_phase55()
        di = r['real_financial_phase55_integration']
        if di['real_records_available'] > 0:
            cm = di.get('confidence_mix', {})
            self.assertEqual(cm.get('manual_fixture', 0), 0)

if __name__ == '__main__':
    unittest.main()
