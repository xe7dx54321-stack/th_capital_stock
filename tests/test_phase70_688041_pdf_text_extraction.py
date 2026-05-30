import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
for p in [str(L), str(J)]:
    if p not in sys.path: sys.path.insert(0, p)
class Test688041PDFText(unittest.TestCase):
    def test_dry_run(self):
        from run_phase70_688041_pdf_text_extraction_hardening import run
        r = run(mode="dry_run"); d = r["phase70_688041_pdf_text_extraction"]
        self.assertEqual(d["mode"], "dry_run")
    def test_no_ocr(self):
        from run_phase70_688041_pdf_text_extraction_hardening import run
        r = run(mode="execute"); d = r["phase70_688041_pdf_text_extraction"]
        self.assertFalse(d.get("ocr_used", True))
    def test_raw_not_saved(self):
        from run_phase70_688041_pdf_text_extraction_hardening import run
        r = run(mode="execute"); d = r["phase70_688041_pdf_text_extraction"]
        self.assertFalse(d.get("raw_pdf_saved", True))
    def test_no_mock_fixture(self):
        from run_phase70_688041_pdf_text_extraction_hardening import run
        r = run(mode="execute"); d = r["phase70_688041_pdf_text_extraction"]
        self.assertFalse(d.get("mock_used",True)); self.assertFalse(d.get("fixture_used",True))
    def test_execute_has_counts(self):
        from run_phase70_688041_pdf_text_extraction_hardening import run
        r = run(mode="execute"); d = r["phase70_688041_pdf_text_extraction"]
        self.assertIn("pdf_text_ok", d); self.assertIn("pdf_text_failed", d)
if __name__ == "__main__": unittest.main()
