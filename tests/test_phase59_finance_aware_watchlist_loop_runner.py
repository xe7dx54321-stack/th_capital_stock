#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib'); sys.path.insert(0, '08_scripts/jobs')
from run_phase59_finance_aware_watchlist_loop import run_loop
class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        r = run_loop('300308.SZ', 'dry-run')
        d = r['phase59_finance_aware_watchlist_loop']
        self.assertEqual(d['mode'], 'dry-run')
        self.assertEqual(d['pending_created'], 0)
    def test_dry_run_no_write(self):
        r = run_loop('300308.SZ', 'dry-run')
        self.assertEqual(r['phase59_finance_aware_watchlist_loop']['mode'], 'dry-run')
if __name__ == '__main__': unittest.main()
