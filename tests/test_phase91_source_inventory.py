import unittest, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase91_source_inventory import build_source_inventory

class TestInventory(unittest.TestCase):
    def test_build(self):
        inv=build_source_inventory()
        s=inv["phase91_existing_source_inventory"]
        self.assertGreater(s["sources_inventoried"],20)
    def test_has_key_sources(self):
        inv=build_source_inventory()
        ids=[s["source_id"] for s in inv["phase91_existing_source_inventory"]["sources"]]
        self.assertIn("akshare_sina_financial",ids)
        self.assertIn("yfinance_financials",ids)
        self.assertIn("sec_edgar",ids)
        self.assertIn("cninfo_300394",ids)
    def test_has_curated_catalogs(self):
        inv=build_source_inventory()
        ids=[s["source_id"] for s in inv["phase91_existing_source_inventory"]["sources"]]
        self.assertIn("ai_optical_keywords",ids)
    def test_has_history_pools(self):
        inv=build_source_inventory()
        ids=[s["source_id"] for s in inv["phase91_existing_source_inventory"]["sources"]]
        self.assertIn("evidence_memory",ids)
