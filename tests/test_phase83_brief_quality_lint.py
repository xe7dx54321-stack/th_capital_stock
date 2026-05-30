import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBriefQualityLint(unittest.TestCase):
    def test_build(self):from build_phase83_brief_quality_lint import build;r=build();l=r["phase83_brief_quality_lint"];self.assertEqual(l["overall_status"],"pass")
    def test_no_system_terms(self):from build_phase83_brief_quality_lint import build;r=build();l=r["phase83_brief_quality_lint"];self.assertEqual(l["system_terms_found"],0)
    def test_no_trade_terms(self):from build_phase83_brief_quality_lint import build;r=build();l=r["phase83_brief_quality_lint"];self.assertEqual(l["trade_advice_terms_found"],0)
    def test_market_scope(self):from build_phase83_brief_quality_lint import build;r=build();l=r["phase83_brief_quality_lint"];self.assertTrue(l["market_scope_explained"])
    def test_no_overclaim(self):from build_phase83_brief_quality_lint import build;r=build();l=r["phase83_brief_quality_lint"];self.assertEqual(l["overclaim_violations"],0)
if __name__=="__main__":unittest.main()
