import unittest, sys; sys.path.insert(0,'08_scripts/lib'); from smr_business_evidence_quality_gate import run_business_evidence_quality_gate
class T(unittest.TestCase):
    def test_gate(self): r=run_business_evidence_quality_gate(); d=r['business_evidence_quality_gate']; self.assertGreater(d['evidence_checked'],0)
    def test_passed_or_review(self): r=run_business_evidence_quality_gate(); d=r['business_evidence_quality_gate']; self.assertGreater(d['passed']+d['review_required'],0)
if __name__=='__main__': unittest.main()
