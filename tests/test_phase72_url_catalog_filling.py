import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestURLCatalogFilling(unittest.TestCase):
    def test_outputs(self):
        from build_phase72_url_catalog_filling_report import build
        r = build(); d = r["phase72_url_catalog_filling"]
        self.assertIn("manual_fill_required_before", d)
    def test_no_empty_url_verified(self):
        from build_phase72_url_catalog_filling_report import build
        r = build(); d = r["phase72_url_catalog_filling"]
        for row in d.get("rows", []):
            if not row.get("candidate_url"):
                self.assertEqual(row.get("url_verification_status"), "manual_fill_required")
    def test_no_mock_fixture(self):
        from build_phase72_url_catalog_filling_report import build
        r = build(); d = r["phase72_url_catalog_filling"]
        self.assertFalse(d.get("mock_used",True)); self.assertFalse(d.get("fixture_used",True))
if __name__ == "__main__": unittest.main()
