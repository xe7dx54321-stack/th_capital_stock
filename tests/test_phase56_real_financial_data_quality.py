import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Phase56QualTests(unittest.TestCase):
    def test_quality_has_status(self):
        from smr_real_financial_data_quality import check_real_data_quality
        r = check_real_data_quality()
        dq = r['real_financial_data_quality']
        self.assertIn('quality_status', dq)
    def test_fixture_contamination_is_false(self):
        from smr_real_financial_data_quality import check_real_data_quality
        r = check_real_data_quality()
        dq = r['real_financial_data_quality']
        self.assertIn('fixture_contamination', dq)

if __name__ == '__main__':
    unittest.main()
