#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'))
from build_phase61_real_business_evidence_watchlist_review import build_real_watchlist_review

class TestRealBusinessWatchlistReview(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = build_real_watchlist_review('300308.SZ')
        d = r['real_business_evidence_watchlist_review']
        self.assertIn('watchlist_decision_update', d)
        self.assertIn('decision_reason', d)

    def test_no_pending_order_trade(self):
        r = build_real_watchlist_review('300308.SZ')
        d = r['real_business_evidence_watchlist_review']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)

    def test_decision_not_buy(self):
        r = build_real_watchlist_review('300308.SZ')
        d = r['real_business_evidence_watchlist_review']
        decision = d['watchlist_decision_update']
        self.assertNotIn('buy', decision.lower())
        self.assertNotIn('sell', decision.lower())

    def test_decision_reasons(self):
        r = build_real_watchlist_review('300308.SZ')
        d = r['real_business_evidence_watchlist_review']
        self.assertGreater(len(d['decision_reason']), 0)

if __name__ == '__main__': unittest.main()
