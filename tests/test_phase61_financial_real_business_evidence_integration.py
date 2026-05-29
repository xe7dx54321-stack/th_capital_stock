#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'))
from build_phase61_financial_real_business_evidence_integration import integrate_financial_real_business

class TestFinancialRealBusinessIntegration(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = integrate_financial_real_business('300308.SZ')
        d = r['financial_real_business_evidence_integration']
        self.assertEqual(d['joint_claims_checked'], 7)
        self.assertTrue(d['real_business_evidence_used'])
        self.assertFalse(d['mock_business_evidence_used'])

    def test_joint_assessments_valid(self):
        r = integrate_financial_real_business('300308.SZ')
        for row in r['financial_real_business_evidence_integration']['rows']:
            self.assertIn(row['joint_assessment'], ['strengthened', 'partially_supported', 'unconfirmed'])
            self.assertIn('financial_side', row)
            self.assertIn('business_side', row)
            self.assertIn('limitation', row)

    def test_no_confirmed_joint(self):
        r = integrate_financial_real_business('300308.SZ')
        for row in r['financial_real_business_evidence_integration']['rows']:
            self.assertNotEqual(row['joint_assessment'], 'confirmed')

    def test_mock_not_used(self):
        r = integrate_financial_real_business('300308.SZ')
        self.assertFalse(r['financial_real_business_evidence_integration']['mock_business_evidence_used'])

if __name__ == '__main__': unittest.main()
