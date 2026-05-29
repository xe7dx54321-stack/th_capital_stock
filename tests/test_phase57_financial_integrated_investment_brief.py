#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
sys.path.insert(0, '08_scripts/reporting')
from build_phase57_financial_integrated_investment_brief import build


class TestIntegratedInvestmentBrief(unittest.TestCase):
    def test_brief_for_300308(self):
        result = build(None, '300308.SZ')
        d = result['financial_integrated_investment_brief']
        self.assertTrue(len(d.get('one_line_conclusion', '')) > 0)
        self.assertGreater(len(d.get('current_observations', [])), 0)

    def test_no_backend_terms(self):
        result = build(None, '300308.SZ')
        d = result['financial_integrated_investment_brief']
        # Only check content fields, not metadata like pending_created
        content_fields = ['one_line_conclusion', 'current_observations',
                          'implications', 'can_conclude', 'cannot_conclude',
                          'current_conclusion']
        text = ''
        for field in content_fields:
            val = d.get(field, '')
            if isinstance(val, list):
                text += ' '.join(str(v) for v in val)
            else:
                text += str(val)
        text = text.lower()
        for term in ['candidate', 'validator']:
            self.assertNotIn(term, text, f'Found backend term: {term}')

    def test_no_teaching_style(self):
        result = build(None, '300308.SZ')
        d = result['financial_integrated_investment_brief']
        text = str(d)
        self.assertNotIn('下一步重点', text)
        self.assertNotIn('建议关注', text)

    def test_no_trade_advice(self):
        result = build(None, '300308.SZ')
        d = result['financial_integrated_investment_brief']
        text = str(d)
        for term in ['buy', 'sell', '买入', '卖出', 'target price', '目标价', '仓位']:
            self.assertNotIn(term, text.lower(), f'Found trade term: {term}')

    def test_financial_data_included(self):
        result = build(None, '300308.SZ')
        d = result['financial_integrated_investment_brief']
        text = str(d['current_observations'])
        self.assertTrue(len(text) > 50, 'Financial data observations should be present')

    def test_cannot_conclude_includes_financial_limits(self):
        result = build(None, '300308.SZ')
        d = result['financial_integrated_investment_brief']
        self.assertGreater(len(d.get('cannot_conclude', [])), 0)

    def test_pending_order_trade_zero(self):
        result = build(None, '300308.SZ')
        d = result['financial_integrated_investment_brief']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)


if __name__ == '__main__':
    unittest.main()
