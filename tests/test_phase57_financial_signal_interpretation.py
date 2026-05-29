#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
from smr_financial_signal_interpretation import interpret_financial_signals


class TestFinancialSignalInterpretation(unittest.TestCase):
    def test_interpretation_for_300308(self):
        result = interpret_financial_signals('300308.SZ')
        d = result['financial_signal_interpretation']
        self.assertIn(d['overall_interpretation'], ['positive_bias', 'negative_bias', 'mixed'])
        self.assertGreater(len(d['observations']), 0)

    def test_observed_first(self):
        result = interpret_financial_signals('300308.SZ')
        d = result['financial_signal_interpretation']
        for o in d['observations']:
            self.assertIn('observation', o)
            self.assertIn('implication', o)
            # observation comes before implication (data first, then meaning)

    def test_no_teaching_style(self):
        result = interpret_financial_signals('300308.SZ')
        d = result['financial_signal_interpretation']
        text = str(d)
        self.assertNotIn('下一步', text)
        self.assertNotIn('建议关注', text)

    def test_confidence_real(self):
        result = interpret_financial_signals('300308.SZ')
        d = result['financial_signal_interpretation']
        for o in d['observations']:
            self.assertNotEqual(o.get('confidence'), 'manual_fixture')


if __name__ == '__main__':
    unittest.main()
