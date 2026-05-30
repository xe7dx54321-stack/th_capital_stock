import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBriefQualityLint(unittest.TestCase):
    def test_lint_pass(self):from build_phase81_brief_quality_lint import build;r=build();l=r["phase81_brief_quality_lint"];self.assertEqual(l["overall_status"],"pass")
    def test_no_system_terms(self):from build_phase81_brief_quality_lint import build;r=build();l=r["phase81_brief_quality_lint"];self.assertEqual(l["system_terms_found"],0);self.assertEqual(l["teaching_phrases_found"],0)
    def test_no_trade_advice(self):from build_phase81_brief_quality_lint import build;r=build();l=r["phase81_brief_quality_lint"];self.assertEqual(l["trade_advice_terms_found"],0);self.assertEqual(l["target_price_terms_found"],0)
    def test_no_overclaim(self):from build_phase81_brief_quality_lint import build;r=build();l=r["phase81_brief_quality_lint"];self.assertEqual(l["overclaim_violations"],0)
    def test_monitoring_boundary(self):from build_phase81_brief_quality_lint import build;r=build();l=r["phase81_brief_quality_lint"];self.assertTrue(l["monitoring_boundary_explained"]);self.assertTrue(l["delta_boundary_explained"]);self.assertTrue(l["anomaly_not_trade_signal"]);self.assertTrue(l["strengthened_not_confirmed"])
if __name__=="__main__":unittest.main()
