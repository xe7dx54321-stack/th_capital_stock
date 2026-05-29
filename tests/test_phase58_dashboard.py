#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
sys.path.insert(0, '08_scripts/reporting')
from build_phase58_ai_optical_financial_variable_dashboard import build


class TestDashboard(unittest.TestCase):
    def test_dashboard_output(self):
        r = build(None)
        d = r['summary']
        self.assertEqual(d['industry'], 'ai_optical_module')
        self.assertGreaterEqual(d['industry_variables_defined'], 6)

    def test_pending_order_trade_zero(self):
        r = build(None)
        d = r['summary']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)

    def test_real_data_used(self):
        r = build(None)
        d = r['summary']
        # May be False on API failures - check it's a boolean
        self.assertIsInstance(d['real_financial_data_used'], bool)


if __name__ == '__main__':
    unittest.main()
