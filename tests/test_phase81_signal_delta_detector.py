import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestDelta(unittest.TestCase):
    def test_detect(self):from smr_phase81_time_series_signal_loader import load_signals;from smr_phase81_time_series_baseline_builder import build_baselines;from smr_phase81_signal_delta_detector import detect_delta;from smr_phase81_monitoring_config import load_config;s=load_signals()["phase81_signal_loader"]["rows"];b=build_baselines(s);c=load_config();d=detect_delta(b,c);rr=d["phase81_signal_delta"];self.assertGreater(rr["signals_checked"],0)
    def test_status_types(self):from smr_phase81_time_series_signal_loader import load_signals;from smr_phase81_time_series_baseline_builder import build_baselines;from smr_phase81_signal_delta_detector import detect_delta;from smr_phase81_monitoring_config import load_config;s=load_signals()["phase81_signal_loader"]["rows"];b=build_baselines(s);c=load_config();d=detect_delta(b,c);statuses=set(r["delta_status"] for r in d["phase81_signal_delta"]["rows"]);self.assertTrue(statuses.issubset({"strengthened","weakened","unchanged","baseline_missing","not_comparable"}))
    def test_baseline_missing_not_unchanged(self):from smr_phase81_signal_delta_detector import detect_delta;from smr_phase81_monitoring_config import load_config;b={"phase81_signal_baseline":{"rows":[{"metric_name":"revenue","baseline_available":False,"latest_value":100,"latest_period":"2025Q3"}]}};c=load_config();d=detect_delta(b,c);self.assertEqual(d["phase81_signal_delta"]["rows"][0]["delta_status"],"baseline_missing")
if __name__=="__main__":unittest.main()
