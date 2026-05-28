#!/usr/bin/env python3
import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

from smr_brief_style_lint import lint_brief, TEACHING_PHRASES
from smr_research_brief_depth_lint import lint_depth
from smr_investment_logic_brief_builder import build_investment_logic_brief

class NoTeachingStyleBriefTests(unittest.TestCase):

    def test_teaching_style_brief_triggers_lint(self):
        teaching_brief = '下一步重点看季报里的收入。需要重点关注毛利率变化。后续应该观察客户份额。建议关注订单量。'
        result = lint_brief(teaching_brief)
        self.assertGreater(result['teaching_phrases_found'], 2)

    def test_observed_first_brief_no_teaching_triggers(self):
        good_brief = '当前已看到高端产品结构改善。这增强了产品升级的判断。目前未取得客户份额数据。不能确认利润弹性。'
        result = lint_brief(good_brief)
        self.assertEqual(result['teaching_phrases_found'], 0)

    def test_depth_lint_teaching_style_warns(self):
        teaching_text = '下一步重点看季报。需要重点关注收入。后续应该观察毛利率。建议关注客户份额。值得关注订单量。'
        result = lint_depth(teaching_text)
        self.assertFalse(result['checks']['no_teaching_style_next_watch'])

    def test_depth_lint_observed_first_passes_teaching_check(self):
        good_text = '当前已看到：产品结构改善。这说明收入质量可能提升。不能确认利润弹性。当前未取得客户份额。'
        result = lint_depth(good_text)
        self.assertTrue(result['checks']['no_teaching_style_next_watch'])

    def test_implication_marker_detected(self):
        text_with_implication = '这说明行业需求强不能直接等同于公司利润弹性确认。'
        result = lint_depth(text_with_implication)
        self.assertTrue(result['checks']['has_implications_from_observations'])

    def test_cannot_conclude_detected(self):
        text = '不能确认公司核心客户份额提升。不能确认ASP和价格趋势。'
        result = lint_depth(text)
        self.assertTrue(result['checks']['has_cannot_conclude_section'])

if __name__ == '__main__':
    unittest.main()
