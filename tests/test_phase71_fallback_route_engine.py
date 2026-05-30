import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestFallbackRoute(unittest.TestCase):
    def test_three_tickers(self):
        from build_phase71_fallback_route_plan import build
        r = build(); plan = r["fallback_route_plan"]
        self.assertEqual(plan["tickers_checked"], 3)
    def test_300394_has_identity_bypass_route(self):
        from build_phase71_fallback_route_plan import build
        r = build(); plan = r["fallback_route_plan"]
        row = [r for r in plan["rows"] if r["ticker"]=="300394.SZ"][0]
        self.assertEqual(row["fallback_mode"], "identity_bypass_text_recovery")
        self.assertIn("irm_szse", row["routes"])
    def test_688041_has_pdf_recovery_route(self):
        from build_phase71_fallback_route_plan import build
        r = build(); plan = r["fallback_route_plan"]
        row = [r for r in plan["rows"] if r["ticker"]=="688041.SH"][0]
        self.assertEqual(row["fallback_mode"], "pdf_text_recovery")
    def test_300308_optional_supplement(self):
        from build_phase71_fallback_route_plan import build
        r = build(); plan = r["fallback_route_plan"]
        row = [r for r in plan["rows"] if r["ticker"]=="300308.SZ"][0]
        self.assertEqual(row["fallback_mode"], "optional_supplement")
if __name__ == "__main__": unittest.main()
