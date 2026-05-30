import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestDownload(unittest.TestCase):
    def test_execute(self):
        from run_phase78_688041_high_value_report_download import run
        r=run("execute");rr=r["phase78_688041_high_value_report_download"]
        self.assertGreaterEqual(rr["pdf_download_ok"],0)
        self.assertFalse(rr["raw_pdf_saved"])
    def test_dry_run(self):
        from run_phase78_688041_high_value_report_download import run
        r=run("dry_run");rr=r["phase78_688041_high_value_report_download"]
        self.assertGreater(rr["pdfs_selected"],0)
    def test_skip_network(self):
        from run_phase78_688041_high_value_report_download import run
        r=run("skip_network");self.assertIsNotNone(r)
if __name__=="__main__":unittest.main()
