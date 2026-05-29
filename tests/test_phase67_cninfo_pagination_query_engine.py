import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_cninfo_pagination_query_engine import query_paginated
class TestPagination(unittest.TestCase):
    def test_dry_run(self):
        r=query_paginated("300308.SZ",max_pages=2,page_size=10,mode="dry_run")
        self.assertEqual(r["cninfo_pagination_inventory"]["status"],"dry_run")
    def test_max_pages_respected(self):
        r=query_paginated("300308.SZ",max_pages=2,page_size=10,mode="dry_run")
        self.assertEqual(r["cninfo_pagination_inventory"]["pages_requested"],2)
    def test_skip_network(self):
        r=query_paginated("300308.SZ",skip_network=True)
        self.assertEqual(r["cninfo_pagination_inventory"]["status"],"skipped_network_disabled")
    def test_identity_map_used(self):
        r=query_paginated("300308.SZ",mode="dry_run")
        self.assertTrue(r["cninfo_pagination_inventory"]["identity_map_used"])
    def test_no_identity_degraded(self):
        r=query_paginated("999999.SZ",mode="dry_run")
        self.assertFalse(r["cninfo_pagination_inventory"]["identity_map_used"])
if __name__=="__main__":unittest.main()
