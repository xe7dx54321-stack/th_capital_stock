#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_controlled_chinese_text_fetcher import fetch_controlled_chinese_texts

class TestControlledTextFetcher(unittest.TestCase):
    def test_dry_run(self):
        r = fetch_controlled_chinese_texts('300308.SZ', 'dry-run')
        d = r['controlled_chinese_text_fetch']
        self.assertEqual(d['text_fetched'], 0)
        self.assertFalse(d['raw_content_saved'])
    def test_skip_network(self):
        r = fetch_controlled_chinese_texts('300308.SZ', 'skip-network', 10)
        d = r['controlled_chinese_text_fetch']
        self.assertGreater(d['text_fetched'], 0)
        self.assertFalse(d['raw_content_saved'])
        self.assertFalse(d['ocr_used'])
    def test_text_rows_have_hash(self):
        r = fetch_controlled_chinese_texts('300308.SZ', 'skip-network', 10)
        for row in r['controlled_chinese_text_fetch']['rows']:
            if row['fetch_status'] in ('text_ok', 'text_ok_real'):
                self.assertIn('text_hash', row)
if __name__=='__main__': unittest.main()
