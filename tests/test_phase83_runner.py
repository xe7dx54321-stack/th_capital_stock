import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestRunner(unittest.TestCase):
    def test_dry_run(self):from run_phase83_hk_us_financial_adapter_pipeline import run;r=run("dry_run");rr=r["phase83_hk_us_financial_adapter_pipeline"];self.assertEqual(rr["mode"],"dry_run")
    def test_execute(self):from run_phase83_hk_us_financial_adapter_pipeline import run;r=run("execute");rr=r["phase83_hk_us_financial_adapter_pipeline"];self.assertEqual(rr["mode"],"execute")
    def test_skip_network(self):from run_phase83_hk_us_financial_adapter_pipeline import run;r=run("skip_network");rr=r["phase83_hk_us_financial_adapter_pipeline"];self.assertEqual(rr["mode"],"skip_network")
    def test_no_pending(self):from run_phase83_hk_us_financial_adapter_pipeline import run;r=run("execute");rr=r["phase83_hk_us_financial_adapter_pipeline"];self.assertEqual(rr["pending_created"],0)
    def test_no_mock(self):from run_phase83_hk_us_financial_adapter_pipeline import run;self.assertTrue(all(not run(m)["phase83_hk_us_financial_adapter_pipeline"]["mock_used"] for m in["dry_run","execute","skip_network"]))
    def test_has_steps(self):from run_phase83_hk_us_financial_adapter_pipeline import run;r=run("execute");self.assertGreater(len(r["phase83_hk_us_financial_adapter_pipeline"]["steps"]),0)
    def test_no_raw(self):from run_phase83_hk_us_financial_adapter_pipeline import run;r=run("execute");self.assertFalse(r["phase83_hk_us_financial_adapter_pipeline"]["raw_saved"])
if __name__=="__main__":unittest.main()
