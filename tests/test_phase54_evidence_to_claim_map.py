import phase54_helpers, unittest; from smr_evidence_to_claim_mapper import build_evidence_map
class Phase54EvidenceMapTests(unittest.TestCase):
    def test_supported_unconfirmed(self):
        r=build_evidence_map("300308.SZ"); m=r["evidence_to_claim_map"]
        self.assertGreater(m["claims_supported"],0)
        self.assertGreater(m["claims_unconfirmed"],0)
    def test_limitations_present(self):
        r=build_evidence_map("300308.SZ"); m=r["evidence_to_claim_map"]
        for row in m["rows"]:
            self.assertGreater(len(row.get("limitations",[])),0)
if __name__=="__main__": unittest.main()
