#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib'); sys.path.insert(0, '08_scripts/reporting')
from build_phase59_finance_aware_watchlist_packet import build

class TestPacket(unittest.TestCase):
    def test_has_sections(self):
        r = build(None, '300308.SZ'); d = r['finance_aware_watchlist_packet']
        self.assertGreater(len(d['what_we_see']), 0)
    def test_no_backend_terms(self):
        r = build(None, '300308.SZ'); text = str(r).lower()
        for t in ['candidate', 'pending_human', 'validator', 'quality gate']:
            self.assertNotIn(t, text)
    def test_no_trade(self):
        r = build(None, '300308.SZ'); d = r['finance_aware_watchlist_packet']
        self.assertEqual(d['pending_created'], 0)
if __name__ == '__main__': unittest.main()
