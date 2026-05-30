import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestFallbackEvidence(unittest.TestCase):
    def test_outputs(self):
        from build_phase71_fallback_evidence_extraction import build
        r = build(); rep = r["fallback_evidence_extraction"]
        self.assertIn("deep_evidence_created", rep)
    def test_management_not_confirmed(self):
        from build_phase71_fallback_evidence_extraction import build
        r = build(); rep = r["fallback_evidence_extraction"]
        for row in rep.get("rows", []):
            if row.get("evidence_strength") == "management_commentary":
                self.assertNotEqual(row.get("limitation", ""), "")
    def test_guard_pass(self):
        from build_phase71_fallback_evidence_extraction import build
        r = build(); rep = r["fallback_evidence_extraction"]
        self.assertEqual(rep["guard_status"], "pass")
    def test_no_mock_fixture(self):
        from build_phase71_fallback_evidence_extraction import build
        r = build(); rep = r["fallback_evidence_extraction"]
        self.assertFalse(rep.get("mock_used",True)); self.assertFalse(rep.get("fixture_used",True))
if __name__ == "__main__": unittest.main()
