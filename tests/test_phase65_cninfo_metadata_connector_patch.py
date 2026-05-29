#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestPhase65MetadataConnectorPatch(unittest.TestCase):
    def test_curated_identity_300308(self):
        from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
        self.assertIn("300308.SZ",CURATED_CNINFO_IDENTITIES)
        self.assertTrue(CURATED_CNINFO_IDENTITIES["300308.SZ"]["org_id"])
    def test_curated_has_plate_column(self):
        from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
        id300=CURATED_CNINFO_IDENTITIES["300308.SZ"]
        self.assertIn("plate",id300)
        self.assertIn("column",id300)
    def test_identity_marked_curated(self):
        from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
        id300=CURATED_CNINFO_IDENTITIES["300308.SZ"]
        self.assertEqual(id300.get("identity_source"),"curated_manifest")
if __name__=="__main__":unittest.main()
