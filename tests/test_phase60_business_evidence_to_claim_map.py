import unittest, sys; sys.path.insert(0,'08_scripts/lib'); from smr_business_evidence_to_claim_mapper import map_business_evidence_to_claims
class T(unittest.TestCase):
    def test_7_claims(self): r=map_business_evidence_to_claims(); self.assertGreaterEqual(r['business_evidence_to_claim_map']['claims_checked'],7)
    def test_has_supported(self): r=map_business_evidence_to_claims(); self.assertGreater(r['business_evidence_to_claim_map']['claims_supported'],0)
    def test_has_unconfirmed(self): r=map_business_evidence_to_claims(); self.assertGreater(r['business_evidence_to_claim_map']['claims_unconfirmed'],0)
if __name__=='__main__': unittest.main()
