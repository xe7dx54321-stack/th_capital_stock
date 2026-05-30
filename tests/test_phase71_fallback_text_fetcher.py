import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestFallbackText(unittest.TestCase):
    def test_outputs(self):
        from build_phase71_fallback_text_fetch_report import build
        r = build(); rep = r.get("fallback_text_fetch_report", r)
        self.assertIn("texts_fetched", rep)
    def test_no_raw(self):
        from build_phase71_fallback_text_fetch_report import build
        r = build(); rep = r.get("fallback_text_fetch_report", r)
        self.assertFalse(rep.get("raw_saved", True))
    def test_no_ocr(self):
        from build_phase71_fallback_text_fetch_report import build
        r = build(); rep = r.get("fallback_text_fetch_report", r)
        self.assertFalse(rep.get("ocr_used", True))
    def test_no_mock_fixture(self):
        from build_phase71_fallback_text_fetch_report import build
        r = build(); rep = r.get("fallback_text_fetch_report", r)
        self.assertFalse(rep.get("mock_used",True)); self.assertFalse(rep.get("fixture_used",True))
if __name__ == "__main__": unittest.main()
