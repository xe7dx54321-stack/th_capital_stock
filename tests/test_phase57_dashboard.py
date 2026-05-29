#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
sys.path.insert(0, '08_scripts/reporting')
from build_phase57_quarterly_financial_refinement_dashboard import build


class TestDashboard(unittest.TestCase):
    def test_dashboard_output(self):
        result = build(None)
        d = result['summary']
        self.assertEqual(d['ticker'], '300308.SZ')
        self.assertIsInstance(d['capex_matched'], bool)
        self.assertIsInstance(d['real_data_used'], bool)
        self.assertGreaterEqual(d['single_quarter_records_created'], 0)

    def test_pending_order_trade_zero(self):
        result = build(None)
        d = result['summary']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)

    def test_real_data_used(self):
        result = build(None)
        d = result['summary']
        self.assertIsInstance(d['real_data_used'], bool)
        self.assertIsInstance(d['fixture_used'], bool)

    def test_has_required_fields(self):
        result = build(None)
        d = result['summary']
        expected = ['ticker', 'capex_matched', 'single_quarter_records_created',
                     'refined_signals_calculated', 'real_data_used', 'fixture_used',
                     'pending_created', 'paper_order_created', 'real_trade_created']
        for key in expected:
            self.assertIn(key, d)


if __name__ == '__main__':
    unittest.main()
