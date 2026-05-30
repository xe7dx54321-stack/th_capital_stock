import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestDailyRunner(unittest.TestCase):
    def test_dry_run(self):from run_phase84_daily_monitoring import run;r=run("dry_run");rr=r["phase84_daily_monitoring_run"];self.assertEqual(rr["run_mode"],"dry_run")
    def test_execute(self):from run_phase84_daily_monitoring import run;r=run("execute");rr=r["phase84_daily_monitoring_run"];self.assertEqual(rr["run_mode"],"execute")
    def test_skip_network(self):from run_phase84_daily_monitoring import run;r=run("skip_network");rr=r["phase84_daily_monitoring_run"];self.assertEqual(rr["run_mode"],"skip_network")
    def test_no_pending(self):from run_phase84_daily_monitoring import run;r=run("execute");rr=r["phase84_daily_monitoring_run"];self.assertEqual(rr["pending_created"],0)
    def test_no_mock(self):from run_phase84_daily_monitoring import run;self.assertTrue(all(not run(m)["phase84_daily_monitoring_run"]["mock_used"] for m in["dry_run","execute","skip_network"]))
    def test_blocked_count(self):from run_phase84_daily_monitoring import run;r=run("execute");rr=r["phase84_daily_monitoring_run"];self.assertEqual(rr["blocked_tickers"],1)
if __name__=="__main__":unittest.main()
