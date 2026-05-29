#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
from smr_financial_cannot_conclude_guard import check_cannot_conclude_guard, FORBIDDEN_CLAIMS, ALLOWED_REWRITES, build_guard_report


class TestCannotConcludeGuard(unittest.TestCase):
    def test_forbidden_claims_detected(self):
        violations = check_cannot_conclude_guard(FORBIDDEN_CLAIMS)
        self.assertGreater(len(violations), 0)

    def test_allowed_rewrites_exist(self):
        for fc in FORBIDDEN_CLAIMS:
            self.assertIn(fc, ALLOWED_REWRITES)

    def test_guard_report_pass(self):
        r = build_guard_report('300308.SZ')
        self.assertEqual(r['cannot_conclude_guard']['guard_status'], 'pass')

    def test_blocks_800g_claim(self):
        violations = check_cannot_conclude_guard(['收入增长证明800G放量'])
        self.assertEqual(len(violations), 1)

    def test_blocks_asp_claim(self):
        violations = check_cannot_conclude_guard(['毛利率强证明ASP改善'])
        self.assertEqual(len(violations), 1)

    def test_clean_text_passes(self):
        violations = check_cannot_conclude_guard(['收入端已经出现明显兑现，但不能单独确认具体产品占比。'])
        self.assertEqual(len(violations), 0)


if __name__ == '__main__':
    unittest.main()
