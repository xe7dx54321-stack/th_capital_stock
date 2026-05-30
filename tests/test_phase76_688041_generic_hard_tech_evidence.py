import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestGenericHardTechEvidence(unittest.TestCase):
    def test_build(self):
        from build_phase76_688041_generic_hard_tech_evidence_rerun import build
        r = build()
        e = r["phase76_688041_generic_hard_tech_evidence_rerun"]
        self.assertGreater(e["deep_evidence_created"], 0)
    def test_not_confirmed(self):
        from build_phase76_688041_generic_hard_tech_evidence_rerun import build
        r = build()
        for row in r["phase76_688041_generic_hard_tech_evidence_rerun"]["rows"]:
            self.assertNotEqual(row["evidence_strength"], "confirmed")
    def test_all_have_limitation(self):
        from build_phase76_688041_generic_hard_tech_evidence_rerun import build
        r = build()
        for row in r["phase76_688041_generic_hard_tech_evidence_rerun"]["rows"]:
            self.assertTrue(row["limitation"])

if __name__ == "__main__": unittest.main()
