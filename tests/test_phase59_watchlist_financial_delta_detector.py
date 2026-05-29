#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
from smr_watchlist_financial_delta_detector import detect_watchlist_financial_delta

class TestDeltaDetector(unittest.TestCase):
    def test_delta_no_previous(self):
        r = detect_watchlist_financial_delta('300308.SZ')
        d = r['watchlist_financial_delta']
        self.assertGreater(d['variables_checked'], 0)
        self.assertEqual(d['note'], 'first_run_baseline_established')

    def test_strengthened_not_confirmed(self):
        r = detect_watchlist_financial_delta('300308.SZ')
        # Check that delta values don't use "confirmed" as a status
        d = r['watchlist_financial_delta']
        for row in d['rows']:
            self.assertNotEqual(row['delta'], 'confirmed')

    def test_has_unjudgeable(self):
        r = detect_watchlist_financial_delta('300308.SZ')
        d = r['watchlist_financial_delta']
        self.assertGreater(d['variables_unjudgeable'], 0)

if __name__ == '__main__': unittest.main()
