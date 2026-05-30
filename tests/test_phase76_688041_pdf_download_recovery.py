import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

class TestPDFDownloadRecovery(unittest.TestCase):
    def test_dry_run(self):
        from run_phase76_688041_pdf_download_recovery import run
        r = run("dry_run")
        dl = r["phase76_688041_pdf_download_recovery"]
        self.assertFalse(dl["network_attempted"])
    def test_skip_network(self):
        from run_phase76_688041_pdf_download_recovery import run
        r = run("skip_network")
        dl = r["phase76_688041_pdf_download_recovery"]
        self.assertEqual(dl["status"], "skip_network")
    def test_no_mock(self):
        from run_phase76_688041_pdf_download_recovery import run
        r = run("dry_run")
        self.assertFalse(r["phase76_688041_pdf_download_recovery"]["mock_used"])

if __name__ == "__main__": unittest.main()
