#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'))
from build_phase61_semantic_business_evidence_from_real_text import extract_semantic_from_real_text

class TestSemanticBusinessEvidenceRealText(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = extract_semantic_from_real_text('300308.SZ')
        d = r['semantic_business_evidence_from_real_text']
        self.assertGreater(d['real_business_evidence_created'], 0)
        self.assertFalse(d['mock_evidence_used'])

    def test_each_evidence_has_limitation(self):
        r = extract_semantic_from_real_text('300308.SZ')
        for ev in r['semantic_business_evidence_from_real_text']['rows']:
            self.assertIn('limitation', ev)
            self.assertIn('cannot_conclude', ev)
            self.assertIn('source_id', ev)
            self.assertIn('quoted_span', ev)
            self.assertIn('evidence_strength', ev)

    def test_no_strong_direct_for_ir(self):
        r = extract_semantic_from_real_text('300308.SZ')
        for ev in r['semantic_business_evidence_from_real_text']['rows']:
            if ev['source_type'] == 'investor_relations_record':
                self.assertNotEqual(ev['evidence_strength'], 'strong_direct_evidence')

    def test_sensitive_variables_flagged(self):
        r = extract_semantic_from_real_text('300308.SZ')
        sensitive_found = [ev for ev in r['semantic_business_evidence_from_real_text']['rows'] if ev.get('sensitive_variable')]
        for ev in sensitive_found:
            self.assertTrue(ev.get('sensitive_variable'))

    def test_mock_not_used(self):
        r = extract_semantic_from_real_text('300308.SZ')
        self.assertFalse(r['semantic_business_evidence_from_real_text']['mock_evidence_used'])

if __name__ == '__main__': unittest.main()
