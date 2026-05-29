#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'))
from build_phase61_real_business_cannot_conclude_guard import run_real_guard
from smr_business_cannot_conclude_guard import BUSINESS_FORBIDDEN, check_business_cannot_conclude

class TestRealBusinessCannotConcludeGuard(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = run_real_guard('300308.SZ')
        d = r['real_business_cannot_conclude_guard']
        self.assertEqual(d['guard_status'], 'pass')
        self.assertEqual(d['violations'], 0)
        self.assertTrue(d['real_evidence_checked'])

    def test_forbidden_fixture_fails(self):
        forbidden = check_business_cannot_conclude([
            '800G提及=800G收入占比确认=> 材料明确说800G收入占比已经确认',
            '毛利率强=ASP改善=> 毛利率走强说明ASP已经改善',
        ])
        self.assertGreater(len(forbidden), 0)

    def test_clean_claims_pass(self):
        clean = check_business_cannot_conclude([
            '800G产品方向有进展信号，但尚未确认收入占比',
            '毛利率数据较强，但不能单独确认ASP改善',
        ])
        self.assertEqual(len(clean), 0)

    def test_forbidden_count(self):
        self.assertEqual(len(BUSINESS_FORBIDDEN), 8)

if __name__ == '__main__': unittest.main()
