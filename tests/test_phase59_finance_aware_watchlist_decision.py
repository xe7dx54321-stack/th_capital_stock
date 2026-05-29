#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
from smr_finance_aware_watchlist_decision import make_finance_aware_watchlist_decision

class TestWatchlistDecision(unittest.TestCase):
    def test_decision_not_buy(self):
        r = make_finance_aware_watchlist_decision('300308.SZ')
        d = r['finance_aware_watchlist_decision']
        self.assertNotIn('buy', d['decision'].lower())
        self.assertNotIn('sell', d['decision'].lower())
    def test_forbidden_actions(self):
        r = make_finance_aware_watchlist_decision('300308.SZ')
        d = r['finance_aware_watchlist_decision']
        self.assertIn('create_trade', d['forbidden_actions'])
    def test_pending_zero(self):
        r = make_finance_aware_watchlist_decision('300308.SZ')
        d = r['finance_aware_watchlist_decision']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)

if __name__ == '__main__': unittest.main()
