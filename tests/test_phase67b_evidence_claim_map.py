import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_deep_evidence_claim_mapper import map_evidence_to_claims
class TestClaimMap(unittest.TestCase):
    def test_unconfirmed_present(self):
        cm=map_evidence_to_claims([])
        self.assertGreater(cm["claims_unconfirmed"],0)
    def test_asp_not_auto_confirmed(self):
        cm=map_evidence_to_claims([])
        for r in cm["rows"]:
            if "asp" in r["claim"]:
                self.assertEqual(r["claim_status"],"unconfirmed")
if __name__=="__main__":unittest.main()
