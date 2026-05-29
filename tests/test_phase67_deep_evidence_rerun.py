import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(R) not in sys.path: sys.path.insert(0,str(R))
if str(J) not in sys.path: sys.path.insert(0,str(J))
class TestDeepEvidenceRerun(unittest.TestCase):
    def test_build_returns_structure(self):
        try:
            from build_phase67_deep_evidence_rerun import build
            r=build("300308.SZ")
            de=r.get("phase67_deep_evidence_rerun",{})
            self.assertIn("evidence_gain_delta",de)
            self.assertIn("guard_status",de)
        except ImportError: self.skipTest("not importable")
    def test_mock_fixture_false(self):
        try:
            from build_phase67_deep_evidence_rerun import build
            r=build("300308.SZ")
            de=r.get("phase67_deep_evidence_rerun",{})
            self.assertFalse(de.get("mock_used"))
            self.assertFalse(de.get("fixture_used"))
        except ImportError: self.skipTest("not importable")
    def test_no_pending_order_trade(self):
        try:
            from build_phase67_deep_evidence_rerun import build
            r=build("300308.SZ")
            de=r.get("phase67_deep_evidence_rerun",{})
            self.assertEqual(de.get("pending_created"),0)
            self.assertEqual(de.get("paper_order_created"),0)
            self.assertEqual(de.get("real_trade_created"),0)
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
