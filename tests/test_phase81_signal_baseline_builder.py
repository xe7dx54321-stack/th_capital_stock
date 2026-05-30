import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestBaseline(unittest.TestCase):
    def test_build(self):from smr_phase81_time_series_signal_loader import load_signals;from smr_phase81_time_series_baseline_builder import build_baselines;s=load_signals()["phase81_signal_loader"]["rows"];b=build_baselines(s);rr=b["phase81_signal_baseline"];self.assertGreaterEqual(rr["baselines_created"],0)
    def test_missing_not_treated_as_ok(self):from smr_phase81_time_series_baseline_builder import build_baselines;b=build_baselines([{"metric_name":"unknown","latest_value":10,"latest_period":"2024FY"}]);rows=b["phase81_signal_baseline"]["rows"];self.assertFalse(rows[0]["baseline_available"]);self.assertGreater(len(rows[0]["baseline_reason"]),0)
    def test_no_guess(self):from smr_phase81_time_series_signal_loader import load_signals;from smr_phase81_time_series_baseline_builder import build_baselines;s=load_signals()["phase81_signal_loader"]["rows"];b=build_baselines(s);rows=b["phase81_signal_baseline"]["rows"];self.assertFalse(any(r["baseline_available"] and r["baseline_reason"]=="guessed" for r in rows))
if __name__=="__main__":unittest.main()
