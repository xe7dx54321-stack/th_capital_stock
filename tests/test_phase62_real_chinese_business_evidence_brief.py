#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
L = R.parents[0] / '08_scripts' / 'lib'
sys.path.insert(0, str(L)); sys.path.insert(0, str(R))
from build_phase62_real_chinese_business_evidence_brief import build

FORBIDDEN = ['candidate', 'pending_human_review', '下一步重点看', '建议关注', '买入', '目标价', '仓位']

class TestBrief(unittest.TestCase):
    def test_returns_valid(self):
        r = build(None, '300308.SZ')
        d = r['real_chinese_business_evidence_brief']
        for k in ['what_we_see', 'what_it_means', 'can_conclude', 'cannot_conclude', 'joint_conclusion']:
            self.assertIn(k, d)
    def test_no_forbidden_terms(self):
        import json
        r = build(None, '300308.SZ')
        d = r['real_chinese_business_evidence_brief']
        content = ' '.join(d.get('what_we_see',[])) + json.dumps(d, ensure_ascii=False)
        for t in FORBIDDEN:
            self.assertNotIn(t, content)
    def test_no_trade(self):
        r = build(None, '300308.SZ')
        d = r['real_chinese_business_evidence_brief']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
if __name__=='__main__': unittest.main()
