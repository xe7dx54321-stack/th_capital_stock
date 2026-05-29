import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestBriefData(unittest.TestCase):
    def test_separates_supported_unconfirmed(self):
        from build_phase68_internal_research_brief_data import build
        r = build('300308.SZ')
        bd = r['internal_research_brief_data']
        self.assertGreater(len(bd['supported_judgments']), 0)
        self.assertGreater(len(bd['unconfirmed_judgments']), 0)
        self.assertGreater(len(bd['source_evidence_refs']), 0)

    def test_cannot_conclude_present(self):
        from build_phase68_internal_research_brief_data import build
        r = build('300308.SZ')
        bd = r['internal_research_brief_data']
        self.assertGreater(len(bd['cannot_conclude']), 0)

class TestBrief(unittest.TestCase):
    def test_no_system_terms(self):
        from build_phase68_internal_research_brief import build
        r = build('300308.SZ')
        md = r['phase68_internal_research_brief']['markdown']
        self.assertNotIn('candidate', md.lower())
        self.assertNotIn('pending', md.lower())
        self.assertNotIn('dashboard', md.lower())
        self.assertNotIn('validator', md.lower())
        self.assertNotIn('runner', md.lower())

    def test_no_trade_advice(self):
        from build_phase68_internal_research_brief import build
        r = build('300308.SZ')
        md = r['phase68_internal_research_brief']['markdown']
        self.assertNotIn('买入', md)
        self.assertNotIn('卖出', md)
        self.assertNotIn('目标价', md)
        self.assertNotIn('仓位', md)
        self.assertNotIn('加仓', md)

    def test_no_teaching(self):
        from build_phase68_internal_research_brief import build
        r = build('300308.SZ')
        md = r['phase68_internal_research_brief']['markdown']
        self.assertNotIn('建议关注', md)
        self.assertNotIn('值得关注', md)
        self.assertNotIn('有望受益', md)

    def test_has_structure(self):
        from build_phase68_internal_research_brief import build
        r = build('300308.SZ')
        md = r['phase68_internal_research_brief']['markdown']
        self.assertIn('老板摘要', md)
        self.assertIn('研究员详情', md)

    def test_supported_not_confirmed(self):
        from build_phase68_internal_research_brief import build
        r = build('300308.SZ')
        md = r['phase68_internal_research_brief']['markdown']
        self.assertIn('不能确认', md)

    def test_asp_not_confirmed(self):
        from build_phase68_internal_research_brief import build
        r = build('300308.SZ')
        md = r['phase68_internal_research_brief']['markdown']
        self.assertNotIn('ASP趋势确认', md)

if __name__ == '__main__': unittest.main()
