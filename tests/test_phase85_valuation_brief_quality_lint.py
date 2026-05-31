import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBriefLint(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_brief_quality_lint import build;r=build();l=r["phase85_valuation_brief_quality_lint"];self.assertEqual(l["overall_status"],"pass")
    def test_no_trade(self):from build_phase85_valuation_brief_quality_lint import build;r=build();l=r["phase85_valuation_brief_quality_lint"];self.assertEqual(l["trade_advice_terms_found"],0)
    def test_low_not_buy(self):from build_phase85_valuation_brief_quality_lint import build;r=build();l=r["phase85_valuation_brief_quality_lint"];self.assertTrue(l["low_not_buy"])
    def test_high_not_sell(self):from build_phase85_valuation_brief_quality_lint import build;r=build();l=r["phase85_valuation_brief_quality_lint"];self.assertTrue(l["high_not_sell"])
if __name__=="__main__":unittest.main()
