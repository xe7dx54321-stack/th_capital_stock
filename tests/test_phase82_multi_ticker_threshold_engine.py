import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestThreshold(unittest.TestCase):
    def test_run(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_time_series_builder import build_time_series;from smr_phase82_multi_ticker_baseline_builder import build_multi_baselines;from smr_phase82_multi_ticker_delta_detector import detect_multi_delta;from smr_phase82_multi_ticker_threshold_engine import run_multi_threshold;m=load_multi_ticker_metrics();s=build_time_series(m);b=build_multi_baselines(s);d=detect_multi_delta(b);r=run_multi_threshold(d);t=r["phase82_multi_ticker_threshold"];self.assertGreater(t["rules_checked"],0)
    def test_not_fake_trigger(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_time_series_builder import build_time_series;from smr_phase82_multi_ticker_baseline_builder import build_multi_baselines;from smr_phase82_multi_ticker_delta_detector import detect_multi_delta;from smr_phase82_multi_ticker_threshold_engine import run_multi_threshold;m=load_multi_ticker_metrics();s=build_time_series(m);b=build_multi_baselines(s);d=detect_multi_delta(b);r=run_multi_threshold(d);rows=r["phase82_multi_ticker_threshold"]["rows"];self.assertTrue(all(row["rule_status"] in{"triggered_strengthened","triggered_weakened","triggered_anomaly","not_triggered","not_comparable"} for row in rows))
if __name__=="__main__":unittest.main()
