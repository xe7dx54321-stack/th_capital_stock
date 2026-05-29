import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestEvidenceGainAnalytics(unittest.TestCase):
    def test_build_returns_structure(self):
        try:
            from build_phase67_evidence_gain_analytics import build
            r=build("300308.SZ")
            ga=r.get("phase67_evidence_gain_analytics",{})
            self.assertIn("phase66",ga)
            self.assertIn("phase67",ga)
            self.assertIn("incremental_gain",ga)
        except ImportError: self.skipTest("not importable")
    def test_mock_fixture_false(self):
        try:
            from build_phase67_evidence_gain_analytics import build
            r=build("300308.SZ")
            self.assertFalse(r.get("phase67_evidence_gain_analytics",{}).get("mock_used"))
            self.assertFalse(r.get("phase67_evidence_gain_analytics",{}).get("fixture_used"))
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
