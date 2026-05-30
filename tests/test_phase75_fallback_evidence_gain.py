import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestPhase75EvidenceGain(unittest.TestCase):
    def test_build(self):
        from build_phase75_fallback_evidence_gain import build
        r = build()
        g = r["phase75_fallback_evidence_gain"]
        self.assertEqual(g["phase74"]["fallback_texts_usable"], 0)
        self.assertEqual(g["phase75"]["fallback_texts_usable"], 0)
    def test_gain_zero_reported_honestly(self):
        from build_phase75_fallback_evidence_gain import build
        r = build()
        g = r["phase75_fallback_evidence_gain"]
        self.assertEqual(g["fallback_evidence_gain_delta"], 0)
        self.assertIn("source_blockers", g)

if __name__ == "__main__":
    unittest.main()
