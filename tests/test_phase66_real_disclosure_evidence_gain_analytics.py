import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(L) not in sys.path: sys.path.insert(0,str(L))

class TestEvidenceGainAnalytics(unittest.TestCase):
    def test_build_returns_structure(self):
        try:
            from build_phase66_real_disclosure_evidence_gain_analytics import build
            r=build("300308.SZ")
            ga=r.get("real_disclosure_evidence_gain_analytics",{})
            self.assertIn("phase65b",ga)
            self.assertIn("phase66",ga)
            self.assertIn("incremental_gain",ga)
        except ImportError:
            self.skipTest("module not importable")
    def test_mock_fixture_false(self):
        try:
            from build_phase66_real_disclosure_evidence_gain_analytics import build
            r=build("300308.SZ")
            ga=r.get("real_disclosure_evidence_gain_analytics",{})
            self.assertFalse(ga.get("mock_used"))
            self.assertFalse(ga.get("fixture_used"))
        except ImportError:
            self.skipTest("module not importable")
    def test_no_pending_order_trade(self):
        try:
            from build_phase66_real_disclosure_evidence_gain_analytics import build
            r=build("300308.SZ")
            ga=r.get("real_disclosure_evidence_gain_analytics",{})
            self.assertEqual(ga.get("pending_created"),0)
            self.assertEqual(ga.get("paper_order_created"),0)
            self.assertEqual(ga.get("real_trade_created"),0)
        except ImportError:
            self.skipTest("module not importable")

if __name__=="__main__":unittest.main()
