#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestPhase65CNINFOStockIdentityResolver(unittest.TestCase):
    def test_skip_network(self):
        from smr_cninfo_stock_identity_resolver import resolve_cninfo_identity
        r=resolve_cninfo_identity("300308.SZ",skip_network=True)
        res=r["cninfo_stock_identity_resolver"]
        self.assertFalse(res["network_attempted"])
        self.assertEqual(res["status"],"skipped_network_disabled")
    def test_has_curated_identity(self):
        from smr_cninfo_stock_identity_resolver import resolve_cninfo_identity
        r=resolve_cninfo_identity("300308.SZ",skip_network=True)
        res=r["cninfo_stock_identity_resolver"]
        self.assertIsNotNone(res.get("curated_identity"))
        self.assertTrue(res["curated_identity"]["org_id"])
    def test_no_mock_no_fixture(self):
        from smr_cninfo_stock_identity_resolver import resolve_cninfo_identity
        r=resolve_cninfo_identity("300308.SZ",skip_network=True)
        res=r["cninfo_stock_identity_resolver"]
        self.assertFalse(res["mock_used"])
        self.assertFalse(res["fixture_used"])
    def test_working_sets_empty_on_skip(self):
        from smr_cninfo_stock_identity_resolver import resolve_cninfo_identity
        r=resolve_cninfo_identity("300308.SZ",skip_network=True)
        res=r["cninfo_stock_identity_resolver"]
        self.assertEqual(len(res["working_parameter_sets"]),0)
if __name__=="__main__":unittest.main()
