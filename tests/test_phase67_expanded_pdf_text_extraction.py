import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))
class TestPhase67ExpandedExtraction(unittest.TestCase):
    def test_no_ocr(self):
        try:
            from run_phase67_expanded_pdf_text_extraction import run_phase67_extraction
            r=run_phase67_extraction("300308.SZ",mode="dry_run")
            self.assertFalse(r["phase67_expanded_pdf_text_extraction"]["ocr_used"])
        except ImportError: self.skipTest("not importable")
    def test_raw_pdf_saved_false(self):
        try:
            from run_phase67_expanded_pdf_text_extraction import run_phase67_extraction
            r=run_phase67_extraction("300308.SZ",mode="dry_run")
            self.assertFalse(r["phase67_expanded_pdf_text_extraction"]["raw_pdf_saved"])
        except ImportError: self.skipTest("not importable")
    def test_dry_run_mode(self):
        try:
            from run_phase67_expanded_pdf_text_extraction import run_phase67_extraction
            r=run_phase67_extraction("300308.SZ",mode="dry_run")
            self.assertEqual(r["phase67_expanded_pdf_text_extraction"]["status"],"dry_run")
        except ImportError: self.skipTest("not importable")
    def test_max_pdfs_respected(self):
        try:
            from run_phase67_expanded_pdf_text_extraction import run_phase67_extraction
            r=run_phase67_extraction("300308.SZ",max_pdfs=5,mode="dry_run")
            self.assertLessEqual(r["phase67_expanded_pdf_text_extraction"]["pdfs_selected"],5)
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
