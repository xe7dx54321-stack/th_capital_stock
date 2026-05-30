import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBriefQualityLint(unittest.TestCase):
    def test_lint_pass(self):from build_phase80_brief_quality_lint import build;r=build();l=r["phase80_brief_quality_lint"];self.assertEqual(l["overall_status"],"pass")
    def test_no_system_terms(self):from build_phase80_brief_quality_lint import build;r=build();l=r["phase80_brief_quality_lint"];self.assertEqual(l["system_terms_found"],0);self.assertEqual(l["teaching_phrases_found"],0)
    def test_no_trade_advice(self):from build_phase80_brief_quality_lint import build;r=build();l=r["phase80_brief_quality_lint"];self.assertEqual(l["trade_advice_terms_found"],0);self.assertEqual(l["target_price_terms_found"],0)
    def test_no_overclaim(self):from build_phase80_brief_quality_lint import build;r=build();l=r["phase80_brief_quality_lint"];self.assertEqual(l["overclaim_violations"],0)
    def test_boundaries_explained(self):from build_phase80_brief_quality_lint import build;r=build();l=r["phase80_brief_quality_lint"];self.assertTrue(l["consistency_boundary_explained"]);self.assertTrue(l["time_series_boundary_explained"])
    def test_observed_not_confirmed(self):from build_phase80_brief_quality_lint import build;r=build();l=r["phase80_brief_quality_lint"];self.assertTrue(l["metric_observed_not_confirmed"])
    def test_no_overclaim_trend(self):from build_phase80_brief_quality_lint import build;r=build();l=r["phase80_brief_quality_lint"];self.assertTrue(l["trend_not_customer_share"]);self.assertTrue(l["gross_margin_not_product_mix_confirmed"]);self.assertTrue(l["R&D_not_commercial_success"])
if __name__=="__main__":unittest.main()
