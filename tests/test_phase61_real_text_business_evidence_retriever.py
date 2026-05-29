#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_real_text_business_evidence_retriever import retrieve_real_text_business_evidence

class TestRealTextRetriever(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = retrieve_real_text_business_evidence('300308.SZ')
        self.assertIn('real_text_business_evidence_retrieval', r)
        d = r['real_text_business_evidence_retrieval']
        self.assertFalse(d['mock_spans_used'])
        self.assertFalse(d['raw_content_saved'])

    def test_has_spans(self):
        r = retrieve_real_text_business_evidence('300308.SZ')
        d = r['real_text_business_evidence_retrieval']
        self.assertGreater(d['candidate_spans_found'], 0)

    def test_all_variables_hit(self):
        r = retrieve_real_text_business_evidence('300308.SZ')
        d = r['real_text_business_evidence_retrieval']
        self.assertIn('800G_product_signal', d['variables_hit'])
        self.assertIn('1_6T_product_signal', d['variables_hit'])

    def test_no_confirmed_in_retrieval(self):
        r = retrieve_real_text_business_evidence('300308.SZ')
        for row in r['real_text_business_evidence_retrieval']['rows']:
            self.assertEqual(row['final_judgment'], 'not_yet_judged')

    def test_spans_have_source_and_quoted(self):
        r = retrieve_real_text_business_evidence('300308.SZ')
        for row in r['real_text_business_evidence_retrieval']['rows']:
            self.assertIn('source_id', row)
            self.assertIn('quoted_span', row)
            self.assertIn('source_type', row)
            self.assertIn('business_variable', row)

if __name__ == '__main__': unittest.main()
