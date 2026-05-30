import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

class TestPhase75Runner(unittest.TestCase):
    def test_dry_run(self):
        from run_phase75_fallback_html_real_execute_and_evidence import run
        r = run("dry_run")
        rr = r["phase75_fallback_html_real_execute_and_evidence"]
        self.assertFalse(rr["network_attempted"])
    def test_execute(self):
        from run_phase75_fallback_html_real_execute_and_evidence import run
        r = run("execute")
        rr = r["phase75_fallback_html_real_execute_and_evidence"]
        self.assertTrue(rr["network_attempted"])
    def test_pending_zero(self):
        from run_phase75_fallback_html_real_execute_and_evidence import run
        r = run("execute")
        self.assertEqual(r["phase75_fallback_html_real_execute_and_evidence"]["pending_created"], 0)
    def test_order_zero(self):
        from run_phase75_fallback_html_real_execute_and_evidence import run
        r = run("execute")
        self.assertEqual(r["phase75_fallback_html_real_execute_and_evidence"]["paper_order_created"], 0)
    def test_trade_zero(self):
        from run_phase75_fallback_html_real_execute_and_evidence import run
        r = run("execute")
        self.assertEqual(r["phase75_fallback_html_real_execute_and_evidence"]["real_trade_created"], 0)
    def test_no_mock(self):
        from run_phase75_fallback_html_real_execute_and_evidence import run
        r = run("execute")
        self.assertFalse(r["phase75_fallback_html_real_execute_and_evidence"]["mock_used"])
    def test_status_degraded(self):
        from run_phase75_fallback_html_real_execute_and_evidence import run
        r = run("execute")
        self.assertIn("degraded", r["phase75_fallback_html_real_execute_and_evidence"]["status"])

if __name__ == "__main__":
    unittest.main()
