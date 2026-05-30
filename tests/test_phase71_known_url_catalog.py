import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestKnownCatalog(unittest.TestCase):
    def test_outputs(self):
        from build_phase71_known_url_catalog import build
        r = build(); cat = r["known_url_catalog"]
        self.assertGreaterEqual(cat["entries_total"], 1)
    def test_empty_url_not_available(self):
        from build_phase71_known_url_catalog import build
        r = build(); cat = r["known_url_catalog"]
        self.assertGreaterEqual(cat["manual_fill_required"], 1)
        self.assertEqual(cat["available"], 0)
    def test_no_mock_fixture(self):
        from build_phase71_known_url_catalog import build
        r = build(); cat = r["known_url_catalog"]
        self.assertFalse(cat.get("mock_used",True)); self.assertFalse(cat.get("fixture_used",True))
if __name__ == "__main__": unittest.main()
