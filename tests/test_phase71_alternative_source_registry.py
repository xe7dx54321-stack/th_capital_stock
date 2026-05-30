import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestAltRegistry(unittest.TestCase):
    def test_has_five_sources(self):
        from build_phase71_alternative_source_registry import build
        r = build(); reg = r["alternative_source_registry"]
        self.assertGreaterEqual(reg["sources_count"], 4)
    def test_covers_irm_exchange_company_catalog(self):
        from build_phase71_alternative_source_registry import build
        r = build(); reg = r["alternative_source_registry"]
        source_ids = [s["source_id"] for s in reg["sources"]]
        for sid in ["irm_szse","szse_disclosure_page","sse_disclosure_page","company_ir_page","known_source_url_catalog"]:
            self.assertIn(sid, source_ids)
    def test_no_mock_fixture(self):
        from build_phase71_alternative_source_registry import build
        r = build(); reg = r["alternative_source_registry"]
        self.assertFalse(reg.get("mock_used",True)); self.assertFalse(reg.get("fixture_used",True))
if __name__ == "__main__": unittest.main()
