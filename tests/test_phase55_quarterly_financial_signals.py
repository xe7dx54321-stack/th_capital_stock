import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
class Phase55SignalCalcTests(unittest.TestCase):
    def test_signals_includes_yoy(self):
        from smr_quarterly_financial_signal_calculator import calculate_quarterly_signals
        r = calculate_quarterly_signals()
        qfs = r['quarterly_financial_signals']
        signals = [s['signal'] for s in qfs['rows']]
        self.assertTrue(any('qoq' in sig for sig in signals))
    def test_signals_includes_qoq(self):
        from smr_quarterly_financial_signal_calculator import calculate_quarterly_signals
        r = calculate_quarterly_signals()
        qfs = r['quarterly_financial_signals']
        signals = [s['signal'] for s in qfs['rows']]
        self.assertTrue(any('qoq' in sig for sig in signals))
    def test_missing_has_reason(self):
        from smr_quarterly_financial_signal_calculator import calculate_quarterly_signals
        r = calculate_quarterly_signals()
        qfs = r['quarterly_financial_signals']
        self.assertIn('missing_reasons', qfs)
    def test_no_yoy_without_comparable(self):
        from smr_quarterly_financial_signal_calculator import calculate_quarterly_signals
        r = calculate_quarterly_signals()
        qfs = r['quarterly_financial_signals']
        self.assertGreater(qfs['signals_calculated'], 0)

if __name__ == '__main__':
    unittest.main()
