import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestClaimMap(unittest.TestCase):
    def test_build(self):
        from build_phase77_688041_pdf_claim_map import build
        r=build();cm=r["phase77_688041_pdf_claim_map"]
        self.assertGreater(cm["claims_context_supported"],0)
        self.assertGreater(cm["claims_unconfirmed"],0)
    def test_no_confirmed(self):
        from build_phase77_688041_pdf_claim_map import build
        r=build();cm=r["phase77_688041_pdf_claim_map"]
        self.assertEqual(cm["claims_supported"],0)
if __name__=="__main__":unittest.main()
