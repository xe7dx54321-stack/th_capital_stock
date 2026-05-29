#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib'); sys.path.insert(0, '08_scripts/reporting')
from build_phase59_finance_aware_watchlist_dashboard import build
class TestDashboard(unittest.TestCase):
    def test_dashboard_keys(self):
        r = build(None); d = r['summary']
        self.assertEqual(d['ticker'], '300308.SZ')
        self.assertIn('decision', d)
    def test_pending_zero(self):
        r = build(None); d = r['summary']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)
    def test_is_instance(self):
        r = build(None)
        self.assertIsInstance(r['summary']['real_financial_data_used'], bool)
if __name__ == '__main__': unittest.main()
