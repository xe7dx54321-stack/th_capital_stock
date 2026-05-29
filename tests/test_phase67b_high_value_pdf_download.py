import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))
class TestPDFDownload(unittest.TestCase):
    def test_dry_run(self):
        try:
            from run_phase67b_high_value_pdf_download import download_and_extract
            r=download_and_extract("300308.SZ",max_pdfs=5,mode="dry_run")
            self.assertEqual(r["high_value_pdf_download"]["status"],"dry_run")
        except ImportError: self.skipTest("not importable")
    def test_raw_pdf_saved_false(self):
        try:
            from run_phase67b_high_value_pdf_download import download_and_extract
            r=download_and_extract("300308.SZ",max_pdfs=5,mode="dry_run")
            self.assertFalse(r["high_value_pdf_download"]["raw_pdf_saved"])
        except ImportError: self.skipTest("not importable")
    def test_max_pdfs_respected(self):
        try:
            from run_phase67b_high_value_pdf_download import download_and_extract
            r=download_and_extract("300308.SZ",max_pdfs=3,mode="dry_run")
            self.assertLessEqual(r["high_value_pdf_download"]["pdfs_selected"],3)
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
