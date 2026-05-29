import unittest, sys; sys.path.insert(0,'08_scripts/lib'); from smr_business_evidence_retriever import retrieve_business_evidence
class T(unittest.TestCase):
    def test_spans(self): r=retrieve_business_evidence(); self.assertGreater(r['business_evidence_retrieval']['candidate_spans_found'],0)
    def test_7_vars(self): r=retrieve_business_evidence(); self.assertGreaterEqual(len(r['business_evidence_retrieval']['variables_hit']),6)
    def test_not_confirmed(self):
        r=retrieve_business_evidence()
        for row in r['business_evidence_retrieval']['rows']: self.assertEqual(row['final_judgment'],'not_yet_judged')
if __name__=='__main__': unittest.main()
