#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestPhase65PDFTextValidation(unittest.TestCase):
    def test_no_raw_no_ocr(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
        from build_phase65_cninfo_pdf_text_validation_report import build
        r=build("300308.SZ")
        v=r.get("cninfo_pdf_text_validation",r)
        self.assertFalse(v.get("raw_pdf_saved",True))
        self.assertFalse(v.get("ocr_used",True))
        self.assertFalse(v.get("mock_used",True))
        self.assertFalse(v.get("fixture_used",True))
if __name__=="__main__":unittest.main()
