import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
if str(R) not in sys.path: sys.path.insert(0, str(R))
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase75BriefQualityLint(unittest.TestCase):
    def test_build(self):
        from build_phase75_brief_quality_lint import build
        r = build()
        lt = r["phase75_brief_quality_lint"]
        self.assertIn(lt["overall_status"], ["pass", "fail"])
    def test_no_trade_terms(self):
        from build_phase75_brief_quality_lint import build
        r = build()
        lt = r["phase75_brief_quality_lint"]
        self.assertEqual(lt["trade_advice_terms_found"], 0)
    def test_management_commentary_not_confirmed(self):
        from build_phase75_brief_quality_lint import build
        r = build()
        lt = r["phase75_brief_quality_lint"]
        self.assertTrue(lt["management_commentary_not_confirmed"])
    def test_company_context_not_strong_direct(self):
        from build_phase75_brief_quality_lint import build
        r = build()
        lt = r["phase75_brief_quality_lint"]
        self.assertTrue(lt["company_context_not_strong_direct"])
    def test_attempt_not_written_as_pass(self):
        from build_phase75_brief_quality_lint import build
        r = build()
        lt = r["phase75_brief_quality_lint"]
        self.assertTrue(lt["attempt_not_written_as_pass"])

if __name__ == "__main__":
    unittest.main()
