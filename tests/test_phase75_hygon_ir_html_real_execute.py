import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

class TestPhase75HygonRealExecute(unittest.TestCase):
    def test_dry_run(self):
        from run_phase75_hygon_ir_html_real_execute import run
        r = run("dry_run")
        self.assertFalse(r["phase75_hygon_ir_html_real_execute"]["network_attempted"])
    def test_network_attempted_execute(self):
        from run_phase75_hygon_ir_html_real_execute import run
        r = run("execute")
        self.assertTrue(r["phase75_hygon_ir_html_real_execute"]["network_attempted"])
    def test_company_context_not_strong_direct(self):
        from run_phase75_hygon_ir_html_real_execute import run
        r = run("dry_run")
        for row in r["phase75_hygon_ir_html_real_execute"].get("rows", [{"allowed_usage": ""}]):
            self.assertNotEqual(row.get("allowed_usage", ""), "strong_direct")
    def test_no_mock(self):
        from run_phase75_hygon_ir_html_real_execute import run
        r = run("dry_run")
        self.assertFalse(r["phase75_hygon_ir_html_real_execute"]["mock_used"])

if __name__ == "__main__":
    unittest.main()
