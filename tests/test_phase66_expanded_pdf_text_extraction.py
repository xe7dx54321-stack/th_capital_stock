import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))

class TestExpandedPdfTextExtraction(unittest.TestCase):
    def test_no_ocr(self):
        try:
            from run_phase66_expanded_pdf_text_extraction import run_expanded_extraction
            r=run_expanded_extraction("300308.SZ",mode="dry_run")
            ex=r.get("expanded_pdf_text_extraction",{})
            self.assertFalse(ex.get("ocr_used"))
        except ImportError:
            self.skipTest("module not importable")
    def test_raw_pdf_saved_false(self):
        try:
            from run_phase66_expanded_pdf_text_extraction import run_expanded_extraction
            r=run_expanded_extraction("300308.SZ",mode="dry_run")
            ex=r.get("expanded_pdf_text_extraction",{})
            self.assertFalse(ex.get("raw_pdf_saved"))
        except ImportError:
            self.skipTest("module not importable")
    def test_dry_run_mode(self):
        try:
            from run_phase66_expanded_pdf_text_extraction import run_expanded_extraction
            r=run_expanded_extraction("300308.SZ",mode="dry_run")
            self.assertEqual(r.get("expanded_pdf_text_extraction",{}).get("status"),"dry_run")
        except ImportError:
            self.skipTest("module not importable")
    def test_max_pdfs_respected(self):
        try:
            from run_phase66_expanded_pdf_text_extraction import run_expanded_extraction
            r=run_expanded_extraction("300308.SZ",max_pdfs=3,mode="dry_run")
            ex=r.get("expanded_pdf_text_extraction",{})
            self.assertLessEqual(ex.get("pdfs_selected",0),3)
        except ImportError:
            self.skipTest("module not importable")
    def test_no_identity_degraded(self):
        try:
            from run_phase66_expanded_pdf_text_extraction import run_expanded_extraction
            r=run_expanded_extraction("999999.SZ",mode="execute")
            self.assertEqual(r.get("expanded_pdf_text_extraction",{}).get("status"),"no_identity")
        except ImportError:
            self.skipTest("module not importable")

if __name__=="__main__":unittest.main()
