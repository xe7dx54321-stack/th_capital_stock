import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestNormalization(unittest.TestCase):
    def test_normalize(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_metric_normalizer import normalize_metrics;m=load_multi_ticker_metrics();r=normalize_metrics(m);n=r["phase82_multi_ticker_metric_normalization"];self.assertGreater(n["metrics_normalized"],0)
    def test_currency_mix(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_metric_normalizer import normalize_metrics;m=load_multi_ticker_metrics();r=normalize_metrics(m);self.assertIn("CNY",r["phase82_multi_ticker_metric_normalization"]["currency_mix"])
if __name__=="__main__":unittest.main()
