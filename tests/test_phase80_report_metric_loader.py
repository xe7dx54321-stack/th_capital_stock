import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestReportLoader(unittest.TestCase):
    def test_load(self):from smr_phase80_report_metric_loader import load_report_metrics;r=load_report_metrics();rr=r["phase80_report_metric_loader"];self.assertGreater(rr["report_metrics_loaded"],0)
    def test_has_period(self):from smr_phase80_report_metric_loader import load_report_metrics;r=load_report_metrics();rows=r["phase80_report_metric_loader"]["rows"];self.assertTrue(all("period" in row and "unit_normalized" in row for row in rows))
    def test_has_revenue(self):from smr_phase80_report_metric_loader import load_report_metrics;r=load_report_metrics();by=r["phase80_report_metric_loader"]["metrics_by_name"];self.assertIn("revenue",by)
if __name__=="__main__":unittest.main()
