import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestEvidenceRerun(unittest.TestCase):
    def test_outputs(self):
        from build_phase72_fallback_evidence_rerun import build
        r = build(); d = r["phase72_fallback_evidence_rerun"]
        self.assertIn("deep_evidence_created", d)
    def test_guard_pass(self):
        from build_phase72_fallback_evidence_rerun import build
        r = build(); d = r["phase72_fallback_evidence_rerun"]
        self.assertEqual(d["guard_status"], "pass")
    def test_no_mock(self):
        from build_phase72_fallback_evidence_rerun import build
        r = build(); d = r["phase72_fallback_evidence_rerun"]
        self.assertFalse(d.get("mock_used",True))
    def test_pending_zero(self):
        from build_phase72_fallback_evidence_rerun import build
        r = build(); d = r["phase72_fallback_evidence_rerun"]
        self.assertEqual(d.get("pending_created", -1), 0)
if __name__ == "__main__": unittest.main()
