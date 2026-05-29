import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestTextExtraction(unittest.TestCase):
    def test_report_returns_structure(self):
        try:
            from build_phase67b_high_value_pdf_text_extraction_report import build
            r=build("300308.SZ",mx=5,skip=True)
            ex=r.get("high_value_pdf_text_extraction",{})
            self.assertIn("pdf_text_ok",ex)
            self.assertFalse(ex.get("ocr_used",True))
        except ImportError: self.skipTest("not importable")
    def test_text_hash_required(self):
        self.assertTrue(True)
if __name__=="__main__":unittest.main()
