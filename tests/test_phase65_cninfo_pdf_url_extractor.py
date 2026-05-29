#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestPhase65PDFUrlExtractor(unittest.TestCase):
    def test_extract_urls_empty(self):
        from smr_cninfo_pdf_url_extractor import extract_pdf_urls_from_metadata
        r=extract_pdf_urls_from_metadata([])
        self.assertEqual(r,[])
    def test_extract_with_url(self):
        from smr_cninfo_pdf_url_extractor import extract_pdf_urls_from_metadata
        rows=[{"id":"1","title":"Test","adjunctUrl":"https://example.com/test.pdf"}]
        r=extract_pdf_urls_from_metadata(rows)
        self.assertEqual(len(r),1)
        self.assertEqual(r[0]["url_status"],"valid_format")
        self.assertTrue(r[0]["pdf_url"].startswith("http"))
    def test_extract_relative_url(self):
        from smr_cninfo_pdf_url_extractor import extract_pdf_urls_from_metadata
        rows=[{"id":"2","title":"Test2","adjunctUrl":"/finalpage/2025-04-25/12345.PDF"}]
        r=extract_pdf_urls_from_metadata(rows)
        self.assertTrue(r[0]["pdf_url"].startswith("http"))
    def test_missing_url(self):
        from smr_cninfo_pdf_url_extractor import extract_pdf_urls_from_metadata
        rows=[{"id":"3","title":"No URL"}]
        r=extract_pdf_urls_from_metadata(rows)
        self.assertEqual(r[0]["url_status"],"missing_or_invalid")
    def test_inventory_no_raw(self):
        from smr_cninfo_pdf_url_extractor import build_pdf_url_inventory
        r=build_pdf_url_inventory("300308.SZ")
        inv=r["cninfo_pdf_url_inventory"]
        self.assertFalse(inv["raw_pdf_saved"])
        self.assertFalse(inv["ocr_used"])
if __name__=="__main__":unittest.main()
