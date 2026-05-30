import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestReconciliation(unittest.TestCase):
    def test_reconcile(self):
        from smr_phase80_report_metric_loader import load_report_metrics
        from smr_phase80_structured_financial_metric_loader import load_structured_metrics
        from smr_phase80_metric_reconciliation import reconcile_metrics
        rm=load_report_metrics()["phase80_report_metric_loader"]["rows"]
        sm=load_structured_metrics()["phase80_structured_metric_loader"]["rows"]
        r=reconcile_metrics(rm,sm);rr=r["phase80_metric_reconciliation"]
        self.assertGreater(rr["matched"],0)
    def test_status_types(self):
        from smr_phase80_report_metric_loader import load_report_metrics
        from smr_phase80_structured_financial_metric_loader import load_structured_metrics
        from smr_phase80_metric_reconciliation import reconcile_metrics
        rm=load_report_metrics()["phase80_report_metric_loader"]["rows"]
        sm=load_structured_metrics()["phase80_structured_metric_loader"]["rows"]
        r=reconcile_metrics(rm,sm);rows=r["phase80_metric_reconciliation"]["rows"]
        statuses=set(row["comparison_status"] for row in rows)
        self.assertIn("matched",statuses)
    def test_mismatch_not_forced(self):
        from smr_phase80_report_metric_loader import load_report_metrics
        from smr_phase80_structured_financial_metric_loader import load_structured_metrics
        from smr_phase80_metric_reconciliation import reconcile_metrics
        rm=[{"metric_name":"revenue","period":"2024FY","value_normalized":100,"unit_normalized":"亿元"}]
        sm=[{"metric_name":"revenue","period":"2024FY","value_normalized":150,"unit_normalized":"亿元"}]
        r=reconcile_metrics(rm,sm);rows=r["phase80_metric_reconciliation"]["rows"]
        self.assertEqual(rows[0]["comparison_status"],"mismatch")
if __name__=="__main__":unittest.main()
