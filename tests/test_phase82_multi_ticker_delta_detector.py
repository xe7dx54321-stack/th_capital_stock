import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestDelta(unittest.TestCase):
    def test_detect(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_time_series_builder import build_time_series;from smr_phase82_multi_ticker_baseline_builder import build_multi_baselines;from smr_phase82_multi_ticker_delta_detector import detect_multi_delta;m=load_multi_ticker_metrics();s=build_time_series(m);b=build_multi_baselines(s);r=detect_multi_delta(b);d=r["phase82_multi_ticker_delta"];self.assertGreater(d["signals_checked"],0)
    def test_status_types(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_time_series_builder import build_time_series;from smr_phase82_multi_ticker_baseline_builder import build_multi_baselines;from smr_phase82_multi_ticker_delta_detector import detect_multi_delta;m=load_multi_ticker_metrics();s=build_time_series(m);b=build_multi_baselines(s);r=detect_multi_delta(b);statuses=set(row["delta_status"] for row in r["phase82_multi_ticker_delta"]["rows"]);self.assertTrue(statuses.issubset({"strengthened","weakened","unchanged","baseline_missing"}))
if __name__=="__main__":unittest.main()
