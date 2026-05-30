import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestLint(unittest.TestCase):
    def test_build(self):
        from build_phase79_brief_quality_lint import build
        r=build();l=r["phase79_brief_quality_lint"]
        self.assertEqual(l["overall_status"],"pass")
    def test_no_trade(self):
        from build_phase79_brief_quality_lint import build
        r=build();l=r["phase79_brief_quality_lint"]
        self.assertEqual(l["trade_advice_terms_found"],0)
        self.assertEqual(l["target_price_terms_found"],0)
    def test_metric_boundaries(self):
        from build_phase79_brief_quality_lint import build
        r=build();l=r["phase79_brief_quality_lint"]
        self.assertTrue(l["metric_observed_not_confirmed"])
        self.assertTrue(l["revenue_not_customer_share"])
        self.assertTrue(l["R&D_not_commercial_success"])
if __name__=="__main__":unittest.main()
