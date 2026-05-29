import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Phase56BriefTests(unittest.TestCase):
    def test_brief_has_boundary(self):
        from smr_real_financial_phase55_integration import integrate_real_with_phase55
        r = integrate_real_with_phase55()
        di = r['real_financial_phase55_integration']
        self.assertEqual(di['pending_created'], 0)
    def test_no_teaching_style(self):
        import json
        from smr_real_financial_phase55_integration import integrate_real_with_phase55
        r = json.dumps(integrate_real_with_phase55(), ensure_ascii=False)
        self.assertNotIn('下一步重点看', r)

if __name__ == '__main__':
    unittest.main()
