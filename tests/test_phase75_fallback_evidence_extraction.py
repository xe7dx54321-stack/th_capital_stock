import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestPhase75EvidenceExtraction(unittest.TestCase):
    def test_build(self):
        from build_phase75_fallback_evidence_extraction import build
        r = build()
        ext = r["phase75_fallback_evidence_extraction"]
        self.assertGreater(ext["deep_evidence_created"], 0)
    def test_management_commentary_not_confirmed(self):
        from build_phase75_fallback_evidence_extraction import build
        r = build()
        for row in r["phase75_fallback_evidence_extraction"]["rows"]:
            self.assertNotEqual(row["evidence_strength"], "confirmed")
    def test_company_context_not_strong_direct(self):
        from build_phase75_fallback_evidence_extraction import build
        r = build()
        for row in r["phase75_fallback_evidence_extraction"]["rows"]:
            self.assertNotEqual(row["evidence_strength"], "strong_direct")

if __name__ == "__main__":
    unittest.main()
