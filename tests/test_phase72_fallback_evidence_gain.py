import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestEvidenceGain(unittest.TestCase):
    def test_outputs(self):
        from build_phase72_fallback_evidence_gain import build
        r = build(); d = r["phase72_fallback_evidence_gain"]
        self.assertIn("fallback_evidence_gain_delta", d)
    def test_gain_zero_ok(self):
        from build_phase72_fallback_evidence_gain import build
        r = build(); d = r["phase72_fallback_evidence_gain"]
        self.assertGreaterEqual(d["fallback_evidence_gain_delta"], 0)
    def test_has_source_blockers(self):
        from build_phase72_fallback_evidence_gain import build
        r = build(); d = r["phase72_fallback_evidence_gain"]
        self.assertIn("source_blockers", d)
    def test_no_mock(self):
        from build_phase72_fallback_evidence_gain import build
        r = build(); d = r["phase72_fallback_evidence_gain"]
        self.assertFalse(d.get("mock_used",True))
    def test_pending_zero(self):
        from build_phase72_fallback_evidence_gain import build
        r = build(); d = r["phase72_fallback_evidence_gain"]
        self.assertEqual(d.get("pending_created", -1), 0)
if __name__ == "__main__": unittest.main()
