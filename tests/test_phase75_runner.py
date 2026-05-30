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
        rr = r["phase75_fallback_html_real_execute_and_evidence"]
        self.assertEqual(rr["pending_created"], 0)
    def test_order_zero(self):
        from run_phase75_fallback_html_real_execute_and_evidence import run
        r = run("execute")
        rr = r["phase75_fallback_html_real_execute_and_evidence"]
        self.assertEqual(rr["paper_order_created"], 0)
    def test_trade_zero(self):
        from run_phase75_fallback_html_real_execute_and_evidence import run
        r = run("execute")
        rr = r["phase75_fallback_html_real_execute_and_evidence"]
        self.assertEqual(rr["real_trade_created"], 0)
    def test_no_mock(self):
        from run_phase75_fallback_html_real_execute_and_evidence import run
        r = run("execute")
        rr = r["phase75_fallback_html_real_execute_and_evidence"]
        self.assertFalse(rr["mock_used"])
    def test_no_fixture(self):
        from run_phase75_fallback_html_real_execute_and_evidence import run
        r = run("execute")
        rr = r["phase75_fallback_html_real_execute_and_evidence"]
        self.assertFalse(rr["fixture_used"])

if __name__ == "__main__":
    unittest.main()
