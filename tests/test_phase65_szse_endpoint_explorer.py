#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestPhase65SZSEEndpointExplorer(unittest.TestCase):
    def test_skip_network(self):
        from smr_szse_endpoint_explorer import explore_szse_endpoints
        r=explore_szse_endpoints("300308.SZ",skip_network=True)
        e=r["szse_endpoint_explorer"]
        self.assertFalse(e["network_attempted"])
        self.assertEqual(e["status"],"skipped")
    def test_no_mock_no_fixture(self):
        from smr_szse_endpoint_explorer import explore_szse_endpoints
        r=explore_szse_endpoints("300308.SZ",skip_network=True)
        e=r["szse_endpoint_explorer"]
        self.assertFalse(e["mock_used"])
        self.assertFalse(e["fixture_used"])
    def test_endpoints_listed(self):
        from smr_szse_endpoint_explorer import SZSE_ENDPOINTS
        self.assertGreater(len(SZSE_ENDPOINTS),0)
if __name__=="__main__":unittest.main()
