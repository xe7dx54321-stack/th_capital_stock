import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
for p in [str(L), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)

class TestPDFURLDiagnostics(unittest.TestCase):
    def test_outputs_structure(self):
        from build_phase70_688041_pdf_url_diagnostics import build
        r = build()
        d = r["phase70_688041_pdf_url_diagnostics"]
        self.assertIn("metadata_sources_checked", d)
        self.assertIn("pdf_urls_found", d)

    def test_no_mock_fixture(self):
        from build_phase70_688041_pdf_url_diagnostics import build
        r = build()
        d = r["phase70_688041_pdf_url_diagnostics"]
        self.assertFalse(d.get("mock_used", True))
        self.assertFalse(d.get("fixture_used", True))

    def test_no_raw_no_ocr(self):
        from build_phase70_688041_pdf_url_diagnostics import build
        r = build()
        d = r["phase70_688041_pdf_url_diagnostics"]
        self.assertFalse(d.get("raw_saved", True))
        self.assertFalse(d.get("ocr_used", True))

    def test_has_failure_classification(self):
        from build_phase70_688041_pdf_url_diagnostics import build
        r = build()
        d = r["phase70_688041_pdf_url_diagnostics"]
        self.assertIn("top_failure_reasons", d)
        self.assertIn("recommended_fix", d)

if __name__ == "__main__": unittest.main()
