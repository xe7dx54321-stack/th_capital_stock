#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals


class TestRefinedQuarterlySignals(unittest.TestCase):
    def test_signals_for_300308(self):
        result = calculate_refined_quarterly_signals('300308.SZ')
        d = result['refined_quarterly_financial_signals']
        self.assertTrue(d['real_data_used'])
        self.assertGreater(d['signals_calculated'], 0)
        self.assertGreater(len(d['latest_signals']), 0)

    def test_has_required_signal_types(self):
        result = calculate_refined_quarterly_signals('300308.SZ')
        d = result['refined_quarterly_financial_signals']
        all_signal_names = set(s['signal'] for s in d.get('all_signals', []))
        expected_subset = {'single_quarter_revenue_yoy', 'single_quarter_net_profit_yoy', 'gross_margin'}
        self.assertTrue(expected_subset.issubset(all_signal_names),
                        f'Missing: {expected_subset - all_signal_names}')

    def test_real_data_used_not_fixture(self):
        result = calculate_refined_quarterly_signals('300308.SZ')
        d = result['refined_quarterly_financial_signals']
        self.assertTrue(d['real_data_used'])
        self.assertFalse(d['fixture_used'])

    def test_derived_confidence(self):
        result = calculate_refined_quarterly_signals('300308.SZ')
        d = result['refined_quarterly_financial_signals']
        for s in d.get('all_signals', []):
            if 'derived' in s['signal'] or 'single_quarter' in s['signal']:
                self.assertIn('derived', s.get('confidence', ''))

    def test_pending_order_trade_zero(self):
        result = calculate_refined_quarterly_signals('300308.SZ')
        d = result['refined_quarterly_financial_signals']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)


if __name__ == '__main__':
    unittest.main()
