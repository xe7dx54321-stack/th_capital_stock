import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestClaimMap(unittest.TestCase):
    def test_build(self):from build_phase80_688041_claim_map_update import build;r=build();cm=r["phase80_688041_claim_map_update"];self.assertGreater(cm["claims_observed"],0);self.assertGreater(cm["claims_unconfirmed"],0)
    def test_no_confirmed(self):from build_phase80_688041_claim_map_update import build;r=build();rows=r["phase80_688041_claim_map_update"]["rows"];[self.assertNotEqual(row["claim_status"],"confirmed") for row in rows]
    def test_all_limitation(self):from build_phase80_688041_claim_map_update import build;r=build();rows=r["phase80_688041_claim_map_update"]["rows"];[self.assertIn("limitation",row) for row in rows]
if __name__=="__main__":unittest.main()
