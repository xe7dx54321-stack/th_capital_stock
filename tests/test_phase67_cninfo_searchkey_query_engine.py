import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_cninfo_searchkey_query_engine import query_by_searchkeys, SEARCHKEY_GROUPS
class TestSearchkey(unittest.TestCase):
    def test_dry_run(self):
        r=query_by_searchkeys("300308.SZ",mode="dry_run")
        self.assertEqual(r["cninfo_searchkey_inventory"]["status"],"dry_run")
    def test_groups_defined(self):
        self.assertGreater(len(SEARCHKEY_GROUPS),0)
    def test_document_type_keywords(self):
        self.assertIn("document_type",SEARCHKEY_GROUPS)
        self.assertIn("投资者关系",SEARCHKEY_GROUPS["document_type"])
    def test_searchkey_hit_not_evidence(self):
        r=query_by_searchkeys("300308.SZ",mode="dry_run")
        self.assertEqual(r["cninfo_searchkey_inventory"]["searchkey_queries_run"],0)
    def test_skip_network(self):
        r=query_by_searchkeys("300308.SZ",skip_network=True)
        self.assertEqual(r["cninfo_searchkey_inventory"]["status"],"skipped_network_disabled")
if __name__=="__main__":unittest.main()
