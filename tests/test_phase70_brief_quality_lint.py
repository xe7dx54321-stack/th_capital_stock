import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestBriefQualityLint(unittest.TestCase):
    def test_lint_pass(self):
        from build_phase70_brief_quality_lint import build
        r = build(); lt = r["phase70_brief_quality_lint"]
        self.assertEqual(lt["overall_status"], "pass")
    def test_system_terms_zero(self):
        from build_phase70_brief_quality_lint import build
        r = build(); lt = r["phase70_brief_quality_lint"]
        self.assertEqual(lt.get("system_terms_found",-1), 0)
    def test_trade_terms_zero(self):
        from build_phase70_brief_quality_lint import build
        r = build(); lt = r["phase70_brief_quality_lint"]
        self.assertEqual(lt.get("trade_advice_terms_found",-1), 0)
    def test_overclaim_zero(self):
        from build_phase70_brief_quality_lint import build
        r = build(); lt = r["phase70_brief_quality_lint"]
        self.assertEqual(lt.get("overclaim_violations",-1), 0)
    def test_no_pass_without_execute(self):
        from build_phase70_brief_quality_lint import build
        r = build(); lt = r["phase70_brief_quality_lint"]
        self.assertTrue(lt.get("no_pass_without_execute", False))
if __name__ == "__main__": unittest.main()
