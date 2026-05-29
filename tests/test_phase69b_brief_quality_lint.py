import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
for p in [str(L), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)

class TestBriefQualityLint(unittest.TestCase):
    def test_lint_pass(self):
        from build_phase69b_brief_quality_lint import build
        r = build()
        lt = r['phase69b_brief_quality_lint']
        self.assertEqual(lt['overall_status'], 'pass')
        self.assertEqual(lt['system_terms_found'], 0)
        self.assertEqual(lt['trade_advice_terms_found'], 0)

    def test_no_system_terms(self):
        from build_phase69b_brief_quality_lint import build
        r = build()
        lt = r['phase69b_brief_quality_lint']
        self.assertEqual(lt.get('system_terms_found', -1), 0)

    def test_no_teaching_phrases(self):
        from build_phase69b_brief_quality_lint import build
        r = build()
        lt = r['phase69b_brief_quality_lint']
        self.assertEqual(lt.get('teaching_phrases_found', -1), 0)

    def test_no_trade_advice_terms(self):
        from build_phase69b_brief_quality_lint import build
        r = build()
        lt = r['phase69b_brief_quality_lint']
        self.assertEqual(lt.get('trade_advice_terms_found', -1), 0)

    def test_no_overclaim(self):
        from build_phase69b_brief_quality_lint import build
        r = build()
        lt = r['phase69b_brief_quality_lint']
        self.assertEqual(lt.get('overclaim_violations', -1), 0)

    def test_no_pass_without_execute(self):
        from build_phase69b_brief_quality_lint import build
        r = build()
        lt = r['phase69b_brief_quality_lint']
        self.assertTrue(lt.get('no_pass_without_execute', False))

    def test_has_boss_summary(self):
        from build_phase69b_brief_quality_lint import build
        r = build()
        lt = r['phase69b_brief_quality_lint']
        self.assertTrue(lt.get('has_boss_summary', False))

if __name__ == '__main__': unittest.main()
