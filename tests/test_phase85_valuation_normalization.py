import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestNormalization(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_normalization_report import build;r=build();n=r["phase85_valuation_normalization"];self.assertGreater(n["tickers_checked"],0)
    def test_currency_mix(self):from build_phase85_valuation_normalization_report import build;r=build();n=r["phase85_valuation_normalization"];self.assertIn("CNY",n["currency_mix"]);self.assertIn("HKD",n["currency_mix"]);self.assertIn("USD",n["currency_mix"])
    def test_no_cross_compare(self):from build_phase85_valuation_normalization_report import build;r=build();n=r["phase85_valuation_normalization"];self.assertIn("N/A",n["currency_mix"])
if __name__=="__main__":unittest.main()
