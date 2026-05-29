import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestPhase67Dashboard(unittest.TestCase):
    def test_build_returns_summary(self):
        try:
            from build_phase67_ir_report_harvest_dashboard import build
            r=build("300308.SZ")
            self.assertIn("summary",r)
        except ImportError: self.skipTest("not importable")
    def test_no_pending_order_trade(self):
        try:
            from build_phase67_ir_report_harvest_dashboard import build
            r=build("300308.SZ")
            s=r.get("summary",{})
            self.assertEqual(s.get("pending_created"),0);self.assertEqual(s.get("paper_order_created"),0);self.assertEqual(s.get("real_trade_created"),0)
        except ImportError: self.skipTest("not importable")
    def test_mock_fixture_false(self):
        try:
            from build_phase67_ir_report_harvest_dashboard import build
            r=build("300308.SZ")
            self.assertFalse(r["summary"]["mock_used"]);self.assertFalse(r["summary"]["fixture_used"])
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
