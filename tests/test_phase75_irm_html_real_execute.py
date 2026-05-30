import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
if str(J) not in sys.path: sys.path.insert(0, str(J))
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase75IRMRealExecute(unittest.TestCase):
    def test_dry_run(self):
        from run_phase75_irm_html_real_execute import run
        r = run("dry_run")
        self.assertFalse(r["phase75_irm_html_real_execute"]["network_attempted"])
    def test_skip_network(self):
        from run_phase75_irm_html_real_execute import run
        r = run("skip_network")
        self.assertFalse(r["phase75_irm_html_real_execute"]["network_attempted"])
    def test_network_attempted_flag_execute(self):
        from run_phase75_irm_html_real_execute import run
        r = run("execute")
        self.assertTrue(r["phase75_irm_html_real_execute"]["network_attempted"])
    def test_no_mock(self):
        from run_phase75_irm_html_real_execute import run
        r = run("dry_run")
        self.assertFalse(r["phase75_irm_html_real_execute"]["mock_used"])
    def test_qa_only_management_commentary(self):
        from run_phase75_irm_html_real_execute import run
        r = run("dry_run")
        for row in r["phase75_irm_html_real_execute"]["rows"]:
            self.assertNotEqual(row.get("allowed_usage", ""), "confirmed")

if __name__ == "__main__":
    unittest.main()
