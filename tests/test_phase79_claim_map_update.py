import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestClaimMap(unittest.TestCase):
    def test_build(self):
        from build_phase79_688041_claim_map_update import build
        r=build();cm=r["phase79_688041_claim_map_update"]
        self.assertGreater(cm["claims_observed"],0)
        self.assertGreater(cm["claims_unconfirmed"],0)
    def test_observed_not_confirmed(self):
        from build_phase79_688041_claim_map_update import build
        r=build();rows=r["phase79_688041_claim_map_update"]["rows"]
        for row in rows:
            if row["claim_status"]=="observed":
                self.assertNotEqual(row["claim_status"],"confirmed")
    def test_all_have_limitation(self):
        from build_phase79_688041_claim_map_update import build
        r=build();rows=r["phase79_688041_claim_map_update"]["rows"]
        for row in rows:self.assertIn("limitation",row)
if __name__=="__main__":unittest.main()
