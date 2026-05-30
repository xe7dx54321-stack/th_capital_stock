import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestLint(unittest.TestCase):
    def test_build(self):from build_phase84_daily_brief_quality_lint import build;r=build();l=r["phase84_daily_brief_quality_lint"];self.assertEqual(l["overall_status"],"pass")
    def test_no_system_terms(self):from build_phase84_daily_brief_quality_lint import build;r=build();l=r["phase84_daily_brief_quality_lint"];self.assertEqual(l["system_terms_found"],0)
    def test_no_trade(self):from build_phase84_daily_brief_quality_lint import build;r=build();l=r["phase84_daily_brief_quality_lint"];self.assertEqual(l["trade_advice_terms_found"],0)
    def test_no_overclaim(self):from build_phase84_daily_brief_quality_lint import build;r=build();l=r["phase84_daily_brief_quality_lint"];self.assertEqual(l["overclaim_violations"],0)
if __name__=="__main__":unittest.main()
