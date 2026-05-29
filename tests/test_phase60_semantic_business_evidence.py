import unittest, sys; sys.path.insert(0,'08_scripts/lib'); from smr_semantic_business_evidence_extractor import extract_semantic_business_evidence
class T(unittest.TestCase):
    def test_evidence(self): r=extract_semantic_business_evidence(); self.assertGreater(r['semantic_business_evidence']['evidence_created'],0)
    def test_limitation(self):
        r=extract_semantic_business_evidence()
        for row in r['semantic_business_evidence']['rows']: self.assertTrue(len(row['limitation'])>0)
    def test_cannot_conclude(self):
        r=extract_semantic_business_evidence()
        for row in r['semantic_business_evidence']['rows']: self.assertGreater(len(row['cannot_conclude']),0)
if __name__=='__main__': unittest.main()
