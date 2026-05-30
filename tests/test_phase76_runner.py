import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        from run_phase76_pdf_recovery_known_url_breakthrough import run
        r = run("dry_run")
        rr = r["phase76_pdf_recovery_known_url_breakthrough"]
        self.assertEqual(rr["mode"], "dry_run")
    def test_execute(self):
        from run_phase76_pdf_recovery_known_url_breakthrough import run
        r = run("execute")
        self.assertTrue(r["phase76_pdf_recovery_known_url_breakthrough"]["brief_quality_status"], "pass")
    def test_pending_zero(self):
        from run_phase76_pdf_recovery_known_url_breakthrough import run
        r = run("execute")
        self.assertEqual(r["phase76_pdf_recovery_known_url_breakthrough"]["pending_created"], 0)
    def test_order_zero(self):
        from run_phase76_pdf_recovery_known_url_breakthrough import run
        r = run("execute")
        self.assertEqual(r["phase76_pdf_recovery_known_url_breakthrough"]["paper_order_created"], 0)
    def test_trade_zero(self):
        from run_phase76_pdf_recovery_known_url_breakthrough import run
        r = run("execute")
        self.assertEqual(r["phase76_pdf_recovery_known_url_breakthrough"]["real_trade_created"], 0)
    def test_no_mock(self):
        from run_phase76_pdf_recovery_known_url_breakthrough import run
        r = run("execute")
        self.assertFalse(r["phase76_pdf_recovery_known_url_breakthrough"]["mock_used"])

if __name__ == "__main__": unittest.main()
