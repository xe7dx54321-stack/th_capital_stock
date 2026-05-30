import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestThreshold(unittest.TestCase):
    def test_run(self):from smr_phase81_time_series_signal_loader import load_signals;from smr_phase81_time_series_baseline_builder import build_baselines;from smr_phase81_signal_delta_detector import detect_delta;from smr_phase81_threshold_rule_engine import run_threshold_rules;from smr_phase81_monitoring_config import load_config;s=load_signals()["phase81_signal_loader"]["rows"];b=build_baselines(s);c=load_config();d=detect_delta(b,c);t=run_threshold_rules(d,c);rr=t["phase81_threshold_rule"];self.assertGreater(rr["rules_checked"],0)
    def test_not_fake_trigger(self):from smr_phase81_time_series_signal_loader import load_signals;from smr_phase81_time_series_baseline_builder import build_baselines;from smr_phase81_signal_delta_detector import detect_delta;from smr_phase81_threshold_rule_engine import run_threshold_rules;from smr_phase81_monitoring_config import load_config;s=load_signals()["phase81_signal_loader"]["rows"];b=build_baselines(s);c=load_config();d=detect_delta(b,c);t=run_threshold_rules(d,c);rows=t["phase81_threshold_rule"]["rows"];self.assertTrue(all(r["rule_status"] in {"triggered_strengthened","triggered_weakened","triggered_anomaly","not_triggered","not_comparable"} for r in rows))
if __name__=="__main__":unittest.main()
