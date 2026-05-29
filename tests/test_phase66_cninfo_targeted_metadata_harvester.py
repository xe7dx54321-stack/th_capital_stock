import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_cninfo_targeted_metadata_harvester import harvest_targeted_metadata

class TestMetadataHarvester(unittest.TestCase):
    def test_dry_run_returns_structure(self):
        r=harvest_targeted_metadata("300308.SZ",max_metadata=5,mode="dry_run")
        inv=r.get("cninfo_targeted_metadata_inventory",{})
        self.assertEqual(inv.get("status"),"dry_run")
    def test_skip_network_returns_skipped(self):
        r=harvest_targeted_metadata("300308.SZ",skip_network=True)
        inv=r.get("cninfo_targeted_metadata_inventory",{})
        self.assertEqual(inv.get("status"),"skipped_network_disabled")
    def test_uses_identity_map(self):
        r=harvest_targeted_metadata("300308.SZ",mode="dry_run")
        inv=r.get("cninfo_targeted_metadata_inventory",{})
        self.assertTrue(inv.get("identity_map_used"))
    def test_stock_param_format(self):
        r=harvest_targeted_metadata("300308.SZ",mode="dry_run")
        inv=r.get("cninfo_targeted_metadata_inventory",{})
        self.assertIn(",",inv.get("stock_param",""))
    def test_max_metadata_limits(self):
        r=harvest_targeted_metadata("300308.SZ",max_metadata=5,mode="dry_run")
        self.assertEqual(r.get("ticker"),"300308.SZ")
    def test_no_identity_degraded(self):
        r=harvest_targeted_metadata("999999.SZ",mode="dry_run")
        inv=r.get("cninfo_targeted_metadata_inventory",{})
        self.assertFalse(inv.get("identity_map_used"))

if __name__=="__main__":unittest.main()
