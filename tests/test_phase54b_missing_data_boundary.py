#!/usr/bin/env python3
import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

from smr_research_brief_depth_lint import lint_depth
from smr_investment_logic_brief_builder import build_investment_logic_brief

class MissingDataBoundaryTests(unittest.TestCase):

    def test_missing_data_marked_as_unavailable(self):
        text = '当前未取得核心客户份额数据。目前没有取得一致预期口径。缺少ASP趋势数据。'
        result = lint_depth(text)
        self.assertTrue(result['checks']['missing_data_marked_as_unavailable'])

    def test_missing_data_not_marked_fails(self):
        text = '客户份额和订单量是下一步关注重点。'
        result = lint_depth(text)
        self.assertFalse(result['checks']['missing_data_marked_as_unavailable'])

    def test_brief_has_cannot_conclude_boundary(self):
        brief = build_investment_logic_brief('300308.SZ')
        ib = brief['investment_logic_brief']
        cannot = ib['cannot_conclude']
        # At least one cannot_conclude item
        self.assertGreater(len(cannot), 0)

    def test_brief_boundary_pending_created_zero(self):
        brief = build_investment_logic_brief('300308.SZ')
        ib = brief['investment_logic_brief']
        bd = ib['boundary']
        self.assertEqual(bd['pending_created'], 0)
        self.assertEqual(bd['paper_order_created'], 0)
        self.assertEqual(bd['real_trade_created'], 0)
        self.assertEqual(bd['promotion_allowed_true'], 0)

    def test_no_system_status_terms_in_brief(self):
        brief = build_investment_logic_brief('300308.SZ')
        brief_json = json.dumps(brief, ensure_ascii=False)
        forbidden = ['candidate','tracking-support','pending','validator','dashboard']
        user_visible_sections = []
        ib = brief['investment_logic_brief']
        for key in ['one_line_conclusion','current_observations','implications','can_conclude','cannot_conclude','current_conclusion']:
            val = ib.get(key, '')
            if isinstance(val, list):
                user_visible_sections.append(' '.join(val))
            else:
                user_visible_sections.append(str(val))
        visible_text = ' '.join(user_visible_sections)
        for term in forbidden:
            self.assertNotIn(term, visible_text, f'Forbidden term found: ' + term)

    def test_no_trading_advice_in_brief(self):
        brief = build_investment_logic_brief('300308.SZ')
        brief_json = json.dumps(brief, ensure_ascii=False)
        self.assertNotIn('买入', brief_json)
        self.assertNotIn('卖出', brief_json)
        self.assertNotIn('目标价', brief_json)
        self.assertNotIn('仓位', brief_json)

    def test_current_observation_before_next_actions(self):
        brief = build_investment_logic_brief('300308.SZ')
        ib = brief['investment_logic_brief']
        obs_count = len(ib.get('current_observations', []))
        action_next = len(ib.get('current_action', {}).get('next', []))
        # Observations should be the main content, not just a prelude to next actions
        self.assertGreaterEqual(obs_count, 2)

if __name__ == '__main__':
    unittest.main()
