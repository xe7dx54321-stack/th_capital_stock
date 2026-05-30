import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestKnownURLPatch(unittest.TestCase):
    def test_has_rows(self):
        from build_phase72_known_url_catalog_patch import build
        r = build(); d = r["phase72_known_url_catalog_patch"]
        self.assertGreaterEqual(len(d["rows"]), 1)
    def test_manual_fill_count(self):
        from build_phase72_known_url_catalog_patch import build
        r = build(); d = r["phase72_known_url_catalog_patch"]
        self.assertGreaterEqual(d["manual_fill_required"], 0)
    def test_no_mock(self):
        from build_phase72_known_url_catalog_patch import build
        r = build(); d = r["phase72_known_url_catalog_patch"]
        self.assertFalse(d.get("mock_used",True))
if __name__ == "__main__": unittest.main()
