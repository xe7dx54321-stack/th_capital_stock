#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'))
from build_phase61_real_business_evidence_to_claim_map import map_real_evidence_to_claims

class TestRealBusinessEvidenceToClaimMap(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = map_real_evidence_to_claims('300308.SZ')
        d = r['real_business_evidence_to_claim_map']
        self.assertEqual(d['claims_checked'], 9)
        self.assertFalse(d['mock_claim_support_used'])

    def test_claims_supported(self):
        r = map_real_evidence_to_claims('300308.SZ')
        d = r['real_business_evidence_to_claim_map']
        self.assertGreater(d['claims_supported'], 0)

    def test_unconfirmed_present(self):
        r = map_real_evidence_to_claims('300308.SZ')
        d = r['real_business_evidence_to_claim_map']
        self.assertGreater(d['claims_unconfirmed'], 0)

    def test_each_claim_has_limitation(self):
        r = map_real_evidence_to_claims('300308.SZ')
        for row in r['real_business_evidence_to_claim_map']['rows']:
            self.assertIn('limitation', row)
            self.assertIn('claim_status', row)

    def test_800G_not_revenue_share(self):
        r = map_real_evidence_to_claims('300308.SZ')
        for row in r['real_business_evidence_to_claim_map']['rows']:
            if '800G' in row['claim'] and 'supported' in row['claim_status']:
                self.assertNotIn('revenue share', row['claim_status'].lower())

if __name__ == '__main__': unittest.main()
