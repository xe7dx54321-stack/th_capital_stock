import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestEvidenceGain(unittest.TestCase):
    def test_outputs(self):
        from build_phase71_fallback_evidence_gain import build
        r = build(); g = r["fallback_evidence_gain"]
        self.assertIn("evidence_gain_delta", g)
    def test_gain_small_or_zero_is_ok(self):
        from build_phase71_fallback_evidence_gain import build
        r = build(); g = r["fallback_evidence_gain"]
        self.assertGreaterEqual(g["evidence_gain_delta"], 0)
    def test_no_mock_fixture(self):
        from build_phase71_fallback_evidence_gain import build
        r = build(); g = r["fallback_evidence_gain"]
        self.assertFalse(g.get("mock_used",True)); self.assertFalse(g.get("fixture_used",True))
    def test_pending_zero(self):
        from build_phase71_fallback_evidence_gain import build
        r = build(); g = r["fallback_evidence_gain"]
        self.assertEqual(g.get("pending_created", -1), 0)
if __name__ == "__main__": unittest.main()
