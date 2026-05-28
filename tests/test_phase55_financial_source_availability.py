import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
class Phase55SourceAvailTests(unittest.TestCase):
    def test_availability_not_equal_to_data(self):
        from smr_financial_source_availability import check_financial_source_availability
        sa = check_financial_source_availability()['financial_source_availability']
        self.assertFalse(sa['structured_data_available'])
    def test_fixture_marked_as_available(self):
        from smr_financial_source_availability import check_financial_source_availability
        sa = check_financial_source_availability()['financial_source_availability']
        self.assertTrue(sa['manual_fixture_available'])
    def test_latest_period_detected(self):
        from smr_financial_source_availability import check_financial_source_availability
        sa = check_financial_source_availability()['financial_source_availability']
        self.assertIsNotNone(sa['latest_period_detected'])

if __name__ == '__main__':
    unittest.main()
