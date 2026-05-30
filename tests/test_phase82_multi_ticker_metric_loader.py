import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestMetricLoader(unittest.TestCase):
    def test_load(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;r=load_multi_ticker_metrics();m=r["phase82_multi_ticker_metric_loader"];self.assertGreater(m["tickers_loaded"],0);self.assertGreater(m["metrics_loaded_total"],0)
    def test_has_market(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;r=load_multi_ticker_metrics();rows=r["phase82_multi_ticker_metric_loader"]["rows"];self.assertTrue(all("market" in row for row in rows))
if __name__=="__main__":unittest.main()
