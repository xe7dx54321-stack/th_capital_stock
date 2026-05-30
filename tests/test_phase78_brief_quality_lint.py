import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestLint(unittest.TestCase):
    def test_build(self):
        from build_phase78_brief_quality_lint import build
        r=build();l=r["phase78_brief_quality_lint"]
        self.assertEqual(l["overall_status"],"pass")
    def test_no_trade(self):
        from build_phase78_brief_quality_lint import build
        r=build();l=r["phase78_brief_quality_lint"]
        self.assertEqual(l["trade_advice_terms_found"],0)
        self.assertEqual(l["target_price_terms_found"],0)
    def test_chinese_boundaries(self):
        from build_phase78_brief_quality_lint import build
        r=build();l=r["phase78_brief_quality_lint"]
        self.assertTrue(l["chinese_keyword_hit_not_confirmed"])
        self.assertTrue(l["observed_not_confirmed"])
        self.assertTrue(l["legal_governance_boundary_preserved"])
if __name__=="__main__":unittest.main()
