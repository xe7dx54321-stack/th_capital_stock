import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestAlignment(unittest.TestCase):
    def test_build(self):
        from build_phase79_qual_quant_alignment import build
        r=build();a=r["phase79_qual_quant_alignment"]
        self.assertEqual(a["variables_checked"],9)
    def test_aligned_not_confirmed(self):
        from build_phase79_qual_quant_alignment import build
        r=build();rows=r["phase79_qual_quant_alignment"]["rows"]
        for row in rows:
            if row["alignment_status"]=="qual_and_quant_aligned":
                self.assertNotIn("confirmed",row["alignment_status"])
    def test_unconfirmed_retained(self):
        from build_phase79_qual_quant_alignment import build
        r=build();a=r["phase79_qual_quant_alignment"]
        self.assertGreater(a["unconfirmed_variables"],0)
if __name__=="__main__":unittest.main()
