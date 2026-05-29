import unittest,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path: sys.path.insert(0,str(R))
class TestGainAnalytics(unittest.TestCase):
    def test_returns_structure(self):
        try:
            from build_phase67b_evidence_gain_analytics import build
            r=build("300308.SZ");ga=r["phase67b_evidence_gain_analytics"]
            self.assertIn("phase66",ga);self.assertIn("phase67b",ga);self.assertIn("incremental",ga)
        except ImportError: self.skipTest("not importable")
    def test_mock_fixture_false(self):
        try:
            from build_phase67b_evidence_gain_analytics import build
            r=build("300308.SZ");ga=r["phase67b_evidence_gain_analytics"]
            self.assertFalse(ga.get("mock_used"));self.assertFalse(ga.get("fixture_used"))
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
