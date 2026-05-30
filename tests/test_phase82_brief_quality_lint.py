import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestLint(unittest.TestCase):
    def test_lint_pass(self):from build_phase82_brief_quality_lint import build;r=build();l=r["phase82_brief_quality_lint"];self.assertEqual(l["overall_status"],"pass")
    def test_no_system_terms(self):from build_phase82_brief_quality_lint import build;r=build();l=r["phase82_brief_quality_lint"];self.assertEqual(l["system_terms_found"],0);self.assertEqual(l["trade_advice_terms_found"],0)
    def test_boundaries(self):from build_phase82_brief_quality_lint import build;r=build();l=r["phase82_brief_quality_lint"];self.assertTrue(l["coverage_boundary_explained"]);self.assertTrue(l["market_scope_explained"]);self.assertTrue(l["blocked_ticker_not_hidden"])
if __name__=="__main__":unittest.main()
