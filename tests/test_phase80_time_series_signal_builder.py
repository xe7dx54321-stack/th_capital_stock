import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestTimeSeries(unittest.TestCase):
    def test_build(self):
        from smr_phase80_report_metric_loader import load_report_metrics
        from smr_phase80_structured_financial_metric_loader import load_structured_metrics
        from smr_phase80_metric_reconciliation import reconcile_metrics
        from smr_phase80_metric_consistency_checker import check_consistency
        from smr_phase80_time_series_signal_builder import build_time_series_signals
        rm=load_report_metrics()["phase80_report_metric_loader"]["rows"]
        sm=load_structured_metrics()["phase80_structured_metric_loader"]["rows"]
        rec=reconcile_metrics(rm,sm)
        cs=check_consistency(rec["phase80_metric_reconciliation"]["rows"])
        r=build_time_series_signals(cs["phase80_metric_consistency"]["rows"],rec["phase80_metric_reconciliation"]["rows"])
        self.assertGreater(r["phase80_time_series_signal"]["signals_created"],0)
    def test_cannot_conclude(self):
        from smr_phase80_report_metric_loader import load_report_metrics
        from smr_phase80_structured_financial_metric_loader import load_structured_metrics
        from smr_phase80_metric_reconciliation import reconcile_metrics
        from smr_phase80_metric_consistency_checker import check_consistency
        from smr_phase80_time_series_signal_builder import build_time_series_signals
        rm=load_report_metrics()["phase80_report_metric_loader"]["rows"]
        sm=load_structured_metrics()["phase80_structured_metric_loader"]["rows"]
        rec=reconcile_metrics(rm,sm)
        cs=check_consistency(rec["phase80_metric_reconciliation"]["rows"])
        r=build_time_series_signals(cs["phase80_metric_consistency"]["rows"],rec["phase80_metric_reconciliation"]["rows"])
        for row in r["phase80_time_series_signal"]["rows"]:self.assertIn("cannot_conclude",row)
if __name__=="__main__":unittest.main()
