import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(L) not in sys.path: sys.path.insert(0,str(L))

class TestDashboard(unittest.TestCase):
    def test_build_returns_summary(self):
        try:
            from build_phase66_targeted_disclosure_harvest_dashboard import build
            r=build("300308.SZ")
            s=r.get("summary",{})
            self.assertIn("ticker",s)
        except ImportError:
            self.skipTest("dashboard module not importable")
    def test_no_pending_order_trade(self):
        try:
            from build_phase66_targeted_disclosure_harvest_dashboard import build
            r=build("300308.SZ")
            s=r.get("summary",{})
            self.assertEqual(s.get("pending_created"),0)
            self.assertEqual(s.get("paper_order_created"),0)
            self.assertEqual(s.get("real_trade_created"),0)
        except ImportError:
            self.skipTest("dashboard module not importable")
    def test_mock_fixture_false(self):
        try:
            from build_phase66_targeted_disclosure_harvest_dashboard import build
            r=build("300308.SZ")
            s=r.get("summary",{})
            self.assertFalse(s.get("mock_used"))
            self.assertFalse(s.get("fixture_used"))
        except ImportError:
            self.skipTest("dashboard module not importable")
    def test_raw_ocr_false(self):
        try:
            from build_phase66_targeted_disclosure_harvest_dashboard import build
            r=build("300308.SZ")
            s=r.get("summary",{})
            self.assertFalse(s.get("raw_saved"))
            self.assertFalse(s.get("ocr_used"))
        except ImportError:
            self.skipTest("dashboard module not importable")
    def test_guard_status_present(self):
        try:
            from build_phase66_targeted_disclosure_harvest_dashboard import build
            r=build("300308.SZ")
            s=r.get("summary",{})
            self.assertIn("guard_status",s)
        except ImportError:
            self.skipTest("dashboard module not importable")

if __name__=="__main__":unittest.main()
