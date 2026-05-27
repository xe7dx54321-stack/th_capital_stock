import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_document_text_extractor import extract_document_text


class Phase29DocumentTextExtractorTests(unittest.TestCase):
    def test_pdf_and_html_extract_clean_text_without_ocr_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "ir.pdf"
            import fitz

            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((72, 72), "问：产能建设如何？\n答：公司推进高速光器件产能建设，以满足客户需求增长。" * 8)
            doc.save(str(pdf_path))
            doc.close()
            source = {"source_id": "pdf1", "ticker": "300394.SZ", "source_url": "https://static.cninfo.com.cn/a.pdf", "local_file_path": str(pdf_path)}
            result = extract_document_text(source)
            self.assertEqual(result["extraction_status"], "text_extracted")
            self.assertEqual(result["document_type"], "pdf")
            self.assertFalse(result["raw_content_saved"])

            html_path = Path(tmp) / "ir.html"
            html_path.write_text("<html><script>x()</script><body><h1>问答</h1><p>答：公司产品结构持续优化，客户需求增长。</p></body></html>", encoding="utf-8")
            html_source = {"source_id": "html1", "ticker": "300394.SZ", "source_url": "https://x/ir.html", "local_file_path": str(html_path)}
            html_result = extract_document_text(html_source)
            self.assertIn(html_result["extraction_status"], {"text_extracted", "text_too_short"})
            self.assertNotIn("script", html_result["text"].lower())

    def test_empty_pdf_marks_scanned_pdf_needs_ocr(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "scan.pdf"
            import fitz

            doc = fitz.open()
            doc.new_page()
            doc.save(str(pdf_path))
            doc.close()
            result = extract_document_text({"source_id": "scan", "source_url": "https://x/scan.pdf", "local_file_path": str(pdf_path)})
            self.assertEqual(result["extraction_status"], "scanned_pdf_needs_ocr")
            self.assertEqual(result["reason"], "pdf text layer is empty; OCR is not enabled by default")


if __name__ == "__main__":
    unittest.main()
