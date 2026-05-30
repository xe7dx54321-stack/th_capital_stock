import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestDownload(unittest.TestCase):
    def test_execute(self):
        from run_phase79_688041_high_value_pdf_real_download_validation import run
        r=run("execute");rr=r["phase79_688041_high_value_pdf_real_download"]
        self.assertEqual(rr["reports_checked"],6)
        self.assertFalse(rr["raw_pdf_saved"])
    def test_dry_run(self):
        from run_phase79_688041_high_value_pdf_real_download_validation import run
        r=run("dry_run");self.assertFalse(r["phase79_688041_high_value_pdf_real_download"]["network_attempted"])
    def test_skip_network(self):
        from run_phase79_688041_high_value_pdf_real_download_validation import run
        r=run("skip_network");self.assertFalse(r["phase79_688041_high_value_pdf_real_download"]["network_attempted"])
    def test_classification(self):
        from run_phase79_688041_high_value_pdf_real_download_validation import run
        r=run("execute");rr=r["phase79_688041_high_value_pdf_real_download"]
        self.assertGreater(rr["pdf_download_ok"],0);self.assertGreater(rr["html_returned"],0);self.assertGreater(rr["encrypted_or_blocked"],0)
if __name__=="__main__":unittest.main()
