#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_chinese_business_text_chunker import chunk_chinese_business_texts

class TestChunker(unittest.TestCase):
    def test_returns_valid(self):
        r = chunk_chinese_business_texts('300308.SZ')
        d = r['chinese_business_text_chunks']
        self.assertGreater(d['chunks_created'], 0)
        self.assertGreater(d['texts_processed'], 0)
    def test_chunks_have_source_id(self):
        r = chunk_chinese_business_texts('300308.SZ')
        for c in r['chinese_business_text_chunks']['rows']:
            self.assertIn('source_id', c)
            self.assertIn('chunk_hash', c)
            self.assertIn('chunk_type', c)
    def test_qa_pairs_present(self):
        r = chunk_chinese_business_texts('300308.SZ')
        types = r['chinese_business_text_chunks']['chunk_types']
        self.assertIn('qa_pair', types)
if __name__=='__main__': unittest.main()
