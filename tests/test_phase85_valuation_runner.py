import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestRunner(unittest.TestCase):
    def test_dry_run(self):from run_phase85_valuation_integration_pipeline import run;r=run("dry_run");rr=r["phase85_valuation_integration_pipeline"];self.assertEqual(rr["mode"],"dry_run")
    def test_execute(self):from run_phase85_valuation_integration_pipeline import run;r=run("execute");rr=r["phase85_valuation_integration_pipeline"];self.assertEqual(rr["mode"],"execute")
    def test_skip_network(self):from run_phase85_valuation_integration_pipeline import run;r=run("skip_network");rr=r["phase85_valuation_integration_pipeline"];self.assertEqual(rr["mode"],"skip_network")
    def test_no_pending(self):from run_phase85_valuation_integration_pipeline import run;r=run("execute");rr=r["phase85_valuation_integration_pipeline"];self.assertEqual(rr["pending_created"],0)
    def test_no_mock(self):from run_phase85_valuation_integration_pipeline import run;self.assertTrue(all(not run(m)["phase85_valuation_integration_pipeline"]["mock_used"] for m in["dry_run","execute","skip_network"]))
    def test_has_steps(self):from run_phase85_valuation_integration_pipeline import run;r=run("execute");self.assertGreater(len(r["phase85_valuation_integration_pipeline"]["steps"]),0)
    def test_no_target_price(self):from run_phase85_valuation_integration_pipeline import run;r=run("execute");self.assertEqual(r["phase85_valuation_integration_pipeline"]["target_price_created"],0)
if __name__=="__main__":unittest.main()
