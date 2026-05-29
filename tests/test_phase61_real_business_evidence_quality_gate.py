#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'))
from build_phase61_real_business_evidence_quality_gate import run_real_quality_gate
from smr_business_evidence_quality_gate import TITLE_ONLY_INDICATORS

class TestRealBusinessEvidenceQualityGate(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = run_real_quality_gate('300308.SZ')
        d = r['real_business_evidence_quality_gate']
        self.assertGreater(d['evidence_checked'], 0)
        self.assertFalse(d['mock_evidence_used'])
        self.assertIn('passed', d)
        self.assertIn('review_required', d)
        self.assertIn('rejected', d)

    def test_sensitive_variables_blocked(self):
        r = run_real_quality_gate('300308.SZ')
        for row in r['real_business_evidence_quality_gate']['rows']:
            if row['quality_status'] == 'review_required':
                self.assertIn('blocked_usages', row)

    def test_passed_not_confirmed(self):
        r = run_real_quality_gate('300308.SZ')
        for row in r['real_business_evidence_quality_gate']['rows']:
            self.assertNotEqual(row['quality_status'], 'confirmed')

    def test_mock_not_used(self):
        r = run_real_quality_gate('300308.SZ')
        self.assertFalse(r['real_business_evidence_quality_gate']['mock_evidence_used'])

if __name__ == '__main__': unittest.main()
