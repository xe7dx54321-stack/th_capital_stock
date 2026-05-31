import unittest, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase91_source_inventory import build_source_inventory
from smr_phase91_source_reality_classifier import classify_sources

class TestClassifier(unittest.TestCase):
    def test_classify_all(self):
        inv=build_source_inventory()
        result=classify_sources(inv)
        r=result["phase91_source_reality_classifier"]
        self.assertEqual(r["sources_classified"],inv["phase91_existing_source_inventory"]["sources_inventoried"])
    def test_curated_catalogs_not_real(self):
        inv=build_source_inventory()
        result=classify_sources(inv)
        for s in result["phase91_source_reality_classifier"]["classified_sources"]:
            if s["source_id"]=="ai_optical_keywords":
                self.assertEqual(s["classified_as"],"curated_catalog_source")
    def test_history_pools_not_live(self):
        inv=build_source_inventory()
        result=classify_sources(inv)
        for s in result["phase91_source_reality_classifier"]["classified_sources"]:
            if s["source_id"]=="evidence_memory":
                self.assertEqual(s["classified_as"],"history_pool_source")
    def test_blocked_not_available(self):
        inv=build_source_inventory()
        result=classify_sources(inv)
        for s in result["phase91_source_reality_classifier"]["classified_sources"]:
            if s["source_id"]=="cninfo_300394":
                self.assertEqual(s["classified_as"],"blocked_source")
    def test_registry_not_source(self):
        inv=build_source_inventory()
        result=classify_sources(inv)
        for s in result["phase91_source_reality_classifier"]["classified_sources"]:
            if s["source_id"]=="phase90_outbox":
                self.assertEqual(s["classified_as"],"registry_only_source")
