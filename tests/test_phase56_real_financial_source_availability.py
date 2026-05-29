import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Phase56AvailTests(unittest.TestCase):
    def test_availability_not_equal_to_data(self):
        from smr_real_financial_source_availability import check_real_source_availability
        r = check_real_source_availability()
        sa = r['real_financial_source_availability']
        self.assertIn('note', sa)
    def test_has_real_structured_flag(self):
        from smr_real_financial_source_availability import check_real_source_availability
        r = check_real_source_availability()
        sa = r['real_financial_source_availability']
        self.assertIn('real_structured_available', sa)

if __name__ == '__main__':
    unittest.main()
