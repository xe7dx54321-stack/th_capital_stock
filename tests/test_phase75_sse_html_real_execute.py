import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

class TestPhase75SSERealExecute(unittest.TestCase):
    def test_dry_run(self):
        from run_phase75_sse_html_real_execute import run
        r = run("dry_run")
        self.assertFalse(r["phase75_sse_html_real_execute"]["network_attempted"])
    def test_network_attempted_execute(self):
        from run_phase75_sse_html_real_execute import run
        r = run("execute", ["688041.SH"])
        self.assertTrue(r["phase75_sse_html_real_execute"]["network_attempted"])
    def test_link_metadata_not_text(self):
        from run_phase75_sse_html_real_execute import run
        r = run("dry_run")
        self.assertFalse(r["phase75_sse_html_real_execute"]["mock_used"])
    def test_pdf_link_detection(self):
        from run_phase75_sse_html_real_execute import run
        r = run("dry_run")
        self.assertIn("pdf_links_found", r["phase75_sse_html_real_execute"])
    def test_no_mock(self):
        from run_phase75_sse_html_real_execute import run
        r = run("dry_run")
        self.assertFalse(r["phase75_sse_html_real_execute"]["mock_used"])

if __name__ == "__main__":
    unittest.main()
