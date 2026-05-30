import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        from run_phase79_high_value_report_quant_pipeline import run
        r=run("dry_run");rr=r["phase79_high_value_report_quant_pipeline"]
        self.assertEqual(rr["mode"],"dry_run")
    def test_execute(self):
        from run_phase79_high_value_report_quant_pipeline import run
        r=run("execute");rr=r["phase79_high_value_report_quant_pipeline"]
        self.assertEqual(rr["pending_created"],0)
        self.assertEqual(rr["paper_order_created"],0)
    def test_no_mock(self):
        from run_phase79_high_value_report_quant_pipeline import run
        r=run("execute");self.assertFalse(r["phase79_high_value_report_quant_pipeline"]["mock_used"])
    def test_skip_network(self):
        from run_phase79_high_value_report_quant_pipeline import run
        r=run("skip_network");self.assertFalse(r["phase79_high_value_report_quant_pipeline"]["real_network_validation_attempted"])
if __name__=="__main__":unittest.main()
