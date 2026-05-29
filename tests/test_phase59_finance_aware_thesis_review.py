#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
from smr_finance_aware_thesis_review import run_finance_aware_thesis_review

class TestThesisReview(unittest.TestCase):
    def test_has_9_claims(self):
        r = run_finance_aware_thesis_review('300308.SZ')
        self.assertEqual(r['finance_aware_thesis_review']['claims_checked'], 9)
    def test_no_pending_allowed(self):
        r = run_finance_aware_thesis_review('300308.SZ')
        self.assertFalse(r['finance_aware_thesis_review']['pending_allowed'])
    def test_has_unconfirmed(self):
        r = run_finance_aware_thesis_review('300308.SZ')
        self.assertGreater(r['finance_aware_thesis_review']['claims_unconfirmed'], 0)

if __name__ == '__main__': unittest.main()
