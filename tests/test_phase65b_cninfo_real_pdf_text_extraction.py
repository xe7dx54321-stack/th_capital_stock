#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class T(unittest.TestCase):
 def test_no_raw_no_ocr(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
  from build_phase65b_cninfo_real_pdf_text_extraction_report import build
  r=build("300308.SZ")
  e=r["cninfo_real_pdf_text_extraction"]
  self.assertFalse(e["raw_pdf_saved"]);self.assertFalse(e["ocr_used"])
  self.assertFalse(e["mock_used"]);self.assertFalse(e["fixture_used"])
 def test_max_pdfs_respected(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
  from build_phase65b_cninfo_real_pdf_text_extraction_report import build
  r=build("300308.SZ")
  self.assertEqual(r["cninfo_real_pdf_text_extraction"]["status"],"requires_network_execution")
if __name__=="__main__":unittest.main()
