import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestClaimMapUpdate(unittest.TestCase):
    def test_build(self):
        from build_phase78_688041_claim_map_update import build
        r=build();cm=r["phase78_688041_claim_map_update"]
        self.assertGreater(cm["claims_observed"],0)
    def test_no_confirmed(self):
        from build_phase78_688041_claim_map_update import build
        r=build();cm=r["phase78_688041_claim_map_update"]
        self.assertEqual(cm["claims_supported"],0)
    def test_differentiate_status(self):
        from build_phase78_688041_claim_map_update import build
        r=build();cm=r["phase78_688041_claim_map_update"]
        self.assertGreater(cm["claims_observed"],0)
        self.assertGreater(cm["claims_context_supported"],0)
        self.assertGreater(cm["claims_unconfirmed"],0)
if __name__=="__main__":unittest.main()
