import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestMasterRunner(unittest.TestCase):
    def test_dry_run(self):from run_phase84_scheduled_daily_monitoring_pipeline import run;r=run("dry_run");rr=r["phase84_scheduled_daily_monitoring_pipeline"];self.assertEqual(rr["mode"],"dry_run")
    def test_execute(self):from run_phase84_scheduled_daily_monitoring_pipeline import run;r=run("execute");rr=r["phase84_scheduled_daily_monitoring_pipeline"];self.assertEqual(rr["mode"],"execute")
    def test_skip_network(self):from run_phase84_scheduled_daily_monitoring_pipeline import run;r=run("skip_network");rr=r["phase84_scheduled_daily_monitoring_pipeline"];self.assertEqual(rr["mode"],"skip_network")
    def test_no_pending(self):from run_phase84_scheduled_daily_monitoring_pipeline import run;r=run("execute");rr=r["phase84_scheduled_daily_monitoring_pipeline"];self.assertEqual(rr["pending_created"],0)
    def test_no_mock(self):from run_phase84_scheduled_daily_monitoring_pipeline import run;self.assertTrue(all(not run(m)["phase84_scheduled_daily_monitoring_pipeline"]["mock_used"] for m in["dry_run","execute","skip_network"]))
    def test_has_steps(self):from run_phase84_scheduled_daily_monitoring_pipeline import run;r=run("execute");self.assertGreater(len(r["phase84_scheduled_daily_monitoring_pipeline"]["steps"]),0)
if __name__=="__main__":unittest.main()
