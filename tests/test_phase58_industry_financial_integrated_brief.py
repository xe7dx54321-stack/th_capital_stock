#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
sys.path.insert(0, '08_scripts/reporting')
from build_phase58_industry_financial_integrated_brief import build


class TestIntegratedBrief(unittest.TestCase):
    def test_brief_outputs(self):
        r = build(None, '300308.SZ')
        d = r['industry_financial_integrated_brief']
        self.assertTrue(len(d.get('one_line_conclusion', '')) > 0)

    def test_no_backend_terms(self):
        r = build(None, '300308.SZ')
        # Only check content fields
        content_fields = ['one_line_conclusion', 'current_observations',
                          'implications', 'can_conclude', 'cannot_conclude',
                          'current_conclusion']
        text = ''
        for f in content_fields:
            val = r['industry_financial_integrated_brief'].get(f, '')
            if isinstance(val, list):
                text += ' '.join(str(v) for v in val)
            else:
                text += str(val)
        for term in ['candidate', 'validator']:
            self.assertNotIn(term, text.lower())

    def test_no_teaching_style(self):
        r = build(None, '300308.SZ')
        text = str(r)
        self.assertNotIn('下一步重点', text)
        self.assertNotIn('建议关注', text)

    def test_no_trade_advice(self):
        r = build(None, '300308.SZ')
        text = str(r).lower()
        for term in ['buy', 'sell', '买入', '卖出', 'target price', '目标价', '仓位']:
            self.assertNotIn(term, text)

    def test_pending_order_trade_zero(self):
        r = build(None, '300308.SZ')
        d = r['industry_financial_integrated_brief']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)


if __name__ == '__main__':
    unittest.main()
