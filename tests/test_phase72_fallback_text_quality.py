import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestTextQuality(unittest.TestCase):
    def test_outputs(self):
        from build_phase72_fallback_text_quality import build
        r = build(); d = r["phase72_fallback_text_quality"]
        self.assertIn("texts_checked", d)
    def test_no_mock(self):
        from build_phase72_fallback_text_quality import build
        r = build(); d = r["phase72_fallback_text_quality"]
        self.assertFalse(d.get("mock_used",True))
    def test_meta_not_usable(self):
        from build_phase72_fallback_text_quality import build
        r = build(); d = r["phase72_fallback_text_quality"]
        self.assertIn("metadata_only", d)
if __name__ == "__main__": unittest.main()
