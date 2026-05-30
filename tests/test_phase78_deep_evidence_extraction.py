import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestDeepEvidence(unittest.TestCase):
    def test_build(self):
        from build_phase78_688041_high_value_deep_evidence import build
        r=build();de=r["phase78_688041_high_value_deep_evidence"]
        self.assertGreater(de["deep_evidence_created"],0)
    def test_each_has_limitation(self):
        from build_phase78_688041_high_value_deep_evidence import build
        r=build();rows=r["phase78_688041_high_value_deep_evidence"]["rows"]
        for row in rows:
            self.assertIn("limitation",row)
            self.assertTrue(len(row["limitation"])>0)
    def test_each_has_cannot_conclude(self):
        from build_phase78_688041_high_value_deep_evidence import build
        r=build();rows=r["phase78_688041_high_value_deep_evidence"]["rows"]
        for row in rows:
            self.assertIn("cannot_conclude",row)
    def test_strong_direct_present(self):
        from build_phase78_688041_high_value_deep_evidence import build
        r=build();de=r["phase78_688041_high_value_deep_evidence"]
        self.assertGreater(de["evidence_strength_mix"].get("strong_direct",0),0)
    def test_no_pending(self):
        from build_phase78_688041_high_value_deep_evidence import build
        r=build();de=r["phase78_688041_high_value_deep_evidence"]
        self.assertEqual(de["pending_created"],0)
        self.assertEqual(de["paper_order_created"],0)
if __name__=="__main__":unittest.main()
