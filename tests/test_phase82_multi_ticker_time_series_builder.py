import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestTimeSeries(unittest.TestCase):
    def test_build(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_time_series_builder import build_time_series;m=load_multi_ticker_metrics();r=build_time_series(m);ts=r["phase82_multi_ticker_time_series_signal"];self.assertGreater(ts["signals_created"],0)
    def test_cannot_conclude(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_time_series_builder import build_time_series;m=load_multi_ticker_metrics();r=build_time_series(m);rows=r["phase82_multi_ticker_time_series_signal"]["rows"];self.assertTrue(all(len(row["cannot_conclude"])>0 for row in rows))
    def test_multi_ticker(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_time_series_builder import build_time_series;m=load_multi_ticker_metrics();r=build_time_series(m);ts=r["phase82_multi_ticker_time_series_signal"];self.assertGreaterEqual(ts["tickers_with_signals"],1)
if __name__=="__main__":unittest.main()
