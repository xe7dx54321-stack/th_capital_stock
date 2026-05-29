#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_cninfo_real_network_fetch_validator import validate_cninfo_network

class TestCNINFO(unittest.TestCase):
    def test_dry_run(self):
        r = validate_cninfo_network('300308.SZ', 'dry-run')
        self.assertEqual(r['cninfo_real_network_validation']['mode'], 'dry-run')
        self.assertFalse(r['cninfo_real_network_validation']['raw_content_saved'])
    def test_skip_network(self):
        r = validate_cninfo_network('300308.SZ', 'skip-network')
        d = r['cninfo_real_network_validation']
        self.assertGreater(d['metadata_sources_found'], 0)
        self.assertFalse(d['ocr_used'])
    def test_execute_degraded_when_no_network(self):
        r = validate_cninfo_network('300308.SZ', 'execute')
        d = r['cninfo_real_network_validation']
        self.assertFalse(d.get('mock_used', True))
        self.assertFalse(d.get('fixture_used', True))
if __name__=='__main__': unittest.main()
