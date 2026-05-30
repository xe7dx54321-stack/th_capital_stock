import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestPhase75EvidenceExtraction(unittest.TestCase):
    def test_build(self):
        from build_phase75_fallback_evidence_extraction import build
        r = build()
        ext = r["phase75_fallback_evidence_extraction"]
        self.assertEqual(ext["deep_evidence_created"], 0)
    def test_rows_have_blockers(self):
        from build_phase75_fallback_evidence_extraction import build
        r = build()
        for row in r["phase75_fallback_evidence_extraction"]["rows"]:
            self.assertIn("blocker", row)
    def test_no_confirmed(self):
        from build_phase75_fallback_evidence_extraction import build
        r = build()
        for row in r["phase75_fallback_evidence_extraction"]["rows"]:
            self.assertNotEqual(row["evidence_strength"], "confirmed")

if __name__ == "__main__":
    unittest.main()
