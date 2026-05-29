#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'))
from build_phase61_real_business_evidence_brief import build_real_brief

FORBIDDEN_TERMS = [
    'candidate', 'pending_human_review', 'validator', 'dashboard', 'quality gate',
    'tracking-support', '下一步重点看', '建议关注', '值得关注',
    '买入', '目标价', '仓位', 'buy', 'sell', 'target price',
]

class TestRealBusinessEvidenceBrief(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = build_real_brief('300308.SZ')
        d = r['real_business_evidence_brief']
        for key in ['what_we_see', 'what_it_means', 'can_conclude', 'cannot_conclude', 'joint_conclusion']:
            self.assertIn(key, d)

    def test_no_forbidden_terms(self):
        r = build_real_brief('300308.SZ')
        d = r['real_business_evidence_brief']
        # Only check content fields, not metadata fields
        content_fields = ['what_we_see', 'what_it_means', 'can_conclude', 'cannot_conclude', 'joint_conclusion']
        all_text = ''
        for key in content_fields:
            val = d[key]
            if isinstance(val, list):
                all_text += ' '.join(val)
            else:
                all_text += str(val)
        for term in FORBIDDEN_TERMS:
            self.assertNotIn(term, all_text, f"Found forbidden term: {term}")

    def test_observed_first(self):
        r = build_real_brief('300308.SZ')
        d = r['real_business_evidence_brief']
        self.assertGreater(len(d['what_we_see']), 0)

    def test_no_trade_advice(self):
        r = build_real_brief('300308.SZ')
        d = r['real_business_evidence_brief']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)
        self.assertTrue(d['real_business_evidence_used'])
        self.assertFalse(d['mock_business_evidence_used'])

if __name__ == '__main__': unittest.main()
