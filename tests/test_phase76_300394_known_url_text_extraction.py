import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

class TestKnownURLTextExtraction(unittest.TestCase):
    def test_dry_run(self):
        from run_phase76_300394_known_url_text_extraction import run
        r = run("dry_run")
        ext = r["phase76_300394_known_url_text_extraction"]
        self.assertEqual(ext["text_extraction_ok"], 0)
    def test_no_ocr(self):
        from run_phase76_300394_known_url_text_extraction import run
        r = run("dry_run")
        self.assertFalse(r["phase76_300394_known_url_text_extraction"]["ocr_used"])
    def test_no_mock(self):
        from run_phase76_300394_known_url_text_extraction import run
        r = run("dry_run")
        self.assertFalse(r["phase76_300394_known_url_text_extraction"]["mock_used"])

if __name__ == "__main__": unittest.main()
