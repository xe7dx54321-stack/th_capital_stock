import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestDiagnostics(unittest.TestCase):
    def test_build(self):
        from build_phase79_failed_report_diagnostics import build
        r=build();d=r["phase79_failed_report_diagnostics"]
        self.assertEqual(d["failed_reports_checked"],3)
    def test_encrypted_not_bypass(self):
        from build_phase79_failed_report_diagnostics import build
        r=build();rows=r["phase79_failed_report_diagnostics"]["rows"]
        for row in rows:
            if row["failure_type"]=="encrypted_pdf":self.assertEqual(row["not_allowed_action"],"bypass_encryption_or_ocr")
    def test_html_not_pdf(self):
        from build_phase79_failed_report_diagnostics import build
        r=build();rows=r["phase79_failed_report_diagnostics"]["rows"]
        for row in rows:
            if row["failure_type"]=="html_returned_instead_of_pdf":self.assertEqual(row["not_allowed_action"],"treat_html_as_pdf_text")
if __name__=="__main__":unittest.main()
