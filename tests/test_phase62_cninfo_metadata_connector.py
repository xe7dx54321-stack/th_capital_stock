#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_cninfo_business_metadata_connector import fetch_cninfo_metadata

class TestCNINFOMetadata(unittest.TestCase):
    def test_dry_run(self):
        r = fetch_cninfo_metadata('300308.SZ', 'dry-run')
        d = r['cninfo_metadata_inventory']
        self.assertEqual(d['sources_found'], 0)
        self.assertFalse(d['network_used'])
        self.assertFalse(d['raw_content_saved'])
    def test_skip_network(self):
        r = fetch_cninfo_metadata('300308.SZ', 'skip-network')
        d = r['cninfo_metadata_inventory']
        self.assertGreater(d['sources_found'], 0)
        self.assertFalse(d['raw_content_saved'])
    def test_metadata_only_flag(self):
        r = fetch_cninfo_metadata('300308.SZ', 'skip-network')
        for row in r['cninfo_metadata_inventory']['rows']:
            self.assertIn('allowed_usage', row)
            self.assertNotIn('real_business_source_text', row['allowed_usage'])
if __name__=='__main__': unittest.main()
