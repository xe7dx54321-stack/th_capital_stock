import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestNormalizer(unittest.TestCase):
    def test_normalize(self):from smr_phase83_hk_us_metric_normalizer import normalize_hk_us_metrics;r=normalize_hk_us_metrics();n=r["phase83_hk_us_metric_normalization"];self.assertGreater(n["metrics_normalized"],0)
    def test_currency_mix(self):from smr_phase83_hk_us_metric_normalizer import normalize_hk_us_metrics;r=normalize_hk_us_metrics();cm=r["phase83_hk_us_metric_normalization"]["currency_mix"];self.assertIn("HKD",cm);self.assertIn("USD",cm)
    def test_no_cny(self):from smr_phase83_hk_us_metric_normalizer import normalize_hk_us_metrics;r=normalize_hk_us_metrics();cm=r["phase83_hk_us_metric_normalization"]["currency_mix"];self.assertNotIn("CNY",cm)
if __name__=="__main__":unittest.main()
