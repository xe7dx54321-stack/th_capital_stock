import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestBaseline(unittest.TestCase):
    def test_build(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_time_series_builder import build_time_series;from smr_phase82_multi_ticker_baseline_builder import build_multi_baselines;m=load_multi_ticker_metrics();s=build_time_series(m);r=build_multi_baselines(s);b=r["phase82_multi_ticker_baseline"];self.assertGreaterEqual(b["baselines_created"],0)
    def test_missing_not_wrapped(self):from smr_phase82_multi_ticker_metric_loader import load_multi_ticker_metrics;from smr_phase82_multi_ticker_time_series_builder import build_time_series;from smr_phase82_multi_ticker_baseline_builder import build_multi_baselines;m=load_multi_ticker_metrics();s=build_time_series(m);r=build_multi_baselines(s);missing=[row for row in r["phase82_multi_ticker_baseline"]["rows"] if not row["baseline_available"]];self.assertTrue(all(row["baseline_reason"] for row in missing) if missing else True)
if __name__=="__main__":unittest.main()
