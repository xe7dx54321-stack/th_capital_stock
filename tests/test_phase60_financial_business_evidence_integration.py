import unittest, sys; sys.path.insert(0,'08_scripts/lib'); from smr_financial_business_evidence_integrator import integrate_financial_business_evidence
class T(unittest.TestCase):
    def test_joint(self): r=integrate_financial_business_evidence(); self.assertGreater(r['financial_business_evidence_integration']['joint_claims_checked'],0)
    def test_has_both(self):
        r=integrate_financial_business_evidence(); d=r['financial_business_evidence_integration']
        self.assertGreater(d['joint_claims_strengthened']+d['joint_claims_partially_supported']+d['joint_claims_unconfirmed'],0)
if __name__=='__main__': unittest.main()
