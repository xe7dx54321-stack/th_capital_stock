#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
from smr_watchlist_industry_financial_signal_adapter import build_watchlist_industry_financial_signal_adapter

class TestAdapter(unittest.TestCase):
    def test_adapter_has_variables(self):
        r = build_watchlist_industry_financial_signal_adapter('300308.SZ')
        d = r['watchlist_industry_financial_signal_adapter']
        self.assertIsInstance(d['industry_variables_loaded'], int)

    def test_guard_status(self):
        r = build_watchlist_industry_financial_signal_adapter('300308.SZ')
        self.assertEqual(r['watchlist_industry_financial_signal_adapter']['cannot_conclude_guard_status'], 'pass')

    def test_pending_zero(self):
        r = build_watchlist_industry_financial_signal_adapter('300308.SZ')
        d = r['watchlist_industry_financial_signal_adapter']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)

if __name__ == '__main__': unittest.main()
