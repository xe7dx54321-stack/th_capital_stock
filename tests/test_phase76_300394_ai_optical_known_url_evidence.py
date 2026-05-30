import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestAIOpticalEvidence(unittest.TestCase):
    def test_build(self):
        from build_phase76_300394_ai_optical_known_url_evidence_rerun import build
        r = build()
        e = r["phase76_300394_ai_optical_known_url_evidence_rerun"]
        self.assertGreater(e["deep_evidence_created"], 0)
    def test_not_strong_direct(self):
        from build_phase76_300394_ai_optical_known_url_evidence_rerun import build
        r = build()
        for row in r["phase76_300394_ai_optical_known_url_evidence_rerun"]["rows"]:
            self.assertNotEqual(row["evidence_strength"], "strong_direct")
    def test_all_have_cannot_conclude(self):
        from build_phase76_300394_ai_optical_known_url_evidence_rerun import build
        r = build()
        for row in r["phase76_300394_ai_optical_known_url_evidence_rerun"]["rows"]:
            self.assertTrue(row["cannot_conclude"])

if __name__ == "__main__": unittest.main()
