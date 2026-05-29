import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Phase56DashTests(unittest.TestCase):
    def test_dashboard_no_pending(self):
        from smr_real_financial_source_availability import check_real_source_availability
        r = check_real_source_availability()
        sa = r['real_financial_source_availability']
        self.assertIsNotNone(sa)
    def test_dashboard_no_trading(self):
        import json
        from smr_real_financial_source_availability import check_real_source_availability
        r = json.dumps(check_real_source_availability(), ensure_ascii=False)
        self.assertNotIn('buy', r.lower())
        self.assertNotIn('sell', r.lower())

if __name__ == '__main__':
    unittest.main()
