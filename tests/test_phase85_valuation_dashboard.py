import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestDashboard(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_integration_dashboard import build;r=build();s=r["summary"];self.assertGreater(s["tickers_total"],0)
    def test_bands(self):from build_phase85_valuation_integration_dashboard import build;r=build();s=r["summary"];self.assertIn("bands",s)
    def test_no_pending(self):from build_phase85_valuation_integration_dashboard import build;r=build();s=r["summary"];self.assertEqual(s["pending_created"],0)
    def test_no_target_price(self):from build_phase85_valuation_integration_dashboard import build;r=build();s=r["summary"];self.assertEqual(s["target_price_created"],0)
if __name__=="__main__":unittest.main()
