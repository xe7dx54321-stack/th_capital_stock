#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib'); sys.path.insert(0, '08_scripts/reporting')
from build_phase59_finance_aware_daily_brief import build
class TestDailyBrief(unittest.TestCase):
    def test_has_all_sections(self):
        r = build(None, '300308.SZ'); d = r['finance_aware_daily_brief']
        self.assertIn('conclusion', d)
    def test_no_teaching(self):
        r = build(None, '300308.SZ')
        self.assertNotIn('下一步', str(r)); self.assertNotIn('建议关注', str(r))
    def test_no_trade(self):
        r = build(None, '300308.SZ'); d = r['finance_aware_daily_brief']
        self.assertEqual(d['pending_created'], 0)
if __name__ == '__main__': unittest.main()
