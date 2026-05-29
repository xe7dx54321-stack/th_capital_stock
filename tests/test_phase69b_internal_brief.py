import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
for p in [str(L), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)

class TestInternalBrief(unittest.TestCase):
    def test_has_structure(self):
        from build_phase69b_internal_brief import build
        r = build()
        md = r['phase69b_internal_brief']['markdown']
        self.assertIn('老板摘要', md)
        self.assertIn('研究员详情', md)

    def test_no_system_terms(self):
        from build_phase69b_internal_brief import build
        r = build()
        md = r['phase69b_internal_brief']['markdown']
        for term in ['candidate', 'pending', 'dashboard', 'validator', 'runner',
                      'mock', 'fixture', 'quality gate', 'pipeline']:
            self.assertNotIn(term, md.lower())

    def test_no_teaching_phrases(self):
        from build_phase69b_internal_brief import build
        r = build()
        md = r['phase69b_internal_brief']['markdown']
        for term in ['建议关注', '值得关注', '有望受益', '未来可期', '下一步重点看']:
            self.assertNotIn(term, md)

    def test_no_trade_advice(self):
        from build_phase69b_internal_brief import build
        r = build()
        md = r['phase69b_internal_brief']['markdown']
        for term in ['买入', '卖出', '目标价', '仓位', '加仓', '减仓']:
            self.assertNotIn(term, md)

    def test_covers_three_tickers(self):
        from build_phase69b_internal_brief import build
        r = build()
        br = r['phase69b_internal_brief']
        self.assertGreaterEqual(br.get('tickers_covered', 0), 2)

    def test_mentions_baseline_regression(self):
        from build_phase69b_internal_brief import build
        r = build()
        md = r['phase69b_internal_brief']['markdown']
        self.assertIn('300308', md)
        self.assertIn('688041', md)
        self.assertIn('300394', md)

if __name__ == '__main__': unittest.main()
