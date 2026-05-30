import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestKnownURLFetch(unittest.TestCase):
    def test_empty_not_fetch(self):
        from build_phase72_known_url_real_fetch_report import build
        r = build(); d = r["phase72_known_url_real_fetch"]
        for row in d.get("rows", []):
            if not row.get("url"): self.assertNotEqual(row.get("text_status"), "text_fetched")
    def test_no_mock(self):
        from build_phase72_known_url_real_fetch_report import build
        r = build(); d = r["phase72_known_url_real_fetch"]
        self.assertFalse(d.get("mock_used",True))
    def test_no_raw(self):
        from build_phase72_known_url_real_fetch_report import build
        r = build(); d = r["phase72_known_url_real_fetch"]
        self.assertFalse(d.get("raw_saved", True))
if __name__ == "__main__": unittest.main()
