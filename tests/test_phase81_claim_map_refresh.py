import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestClaimMapRefresh(unittest.TestCase):
    def test_build(self):from build_phase81_688041_claim_map_refresh import build;r=build();cm=r["phase81_688041_claim_map_refresh"];self.assertGreater(cm["claims_observed"],0);self.assertGreater(cm["claims_unconfirmed"],0)
    def test_no_confirmed(self):from build_phase81_688041_claim_map_refresh import build;r=build();rows=r["phase81_688041_claim_map_refresh"]["rows"];self.assertTrue(all(row["claim_status"]!="confirmed" for row in rows))
    def test_strengthened_not_confirmed(self):from build_phase81_688041_claim_map_refresh import build;r=build();rows=r["phase81_688041_claim_map_refresh"]["rows"];sr=[row for row in rows if row["claim_status"]=="strengthened"];self.assertTrue(all("does not confirm" in row["limitation"] for row in sr))
if __name__=="__main__":unittest.main()
