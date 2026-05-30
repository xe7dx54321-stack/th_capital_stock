import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
for p in [str(L), str(R)]: 
    if p not in sys.path: sys.path.insert(0, p)
class TestCuratedIdentityPatch(unittest.TestCase):
    def test_no_fake_write_on_no_orgid(self):
        from build_phase70_300394_curated_identity_patch import build
        r = build(); d = r["phase70_300394_curated_identity_patch"]
        if not d["identity_patch_applied"]:
            self.assertIsNotNone(d.get("reason"))
    def test_no_reuse_other_ticker_org_id(self):
        from build_phase70_300394_curated_identity_patch import build
        from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
        r = build(); d = r["phase70_300394_curated_identity_patch"]
        if d["identity_patch_applied"]:
            org308 = CURATED_CNINFO_IDENTITIES.get("300308.SZ",{}).get("org_id","")
            self.assertNotEqual(d.get("org_id"), org308)
    def test_ticker_specific(self):
        from build_phase70_300394_curated_identity_patch import build
        r = build(); d = r["phase70_300394_curated_identity_patch"]
        self.assertTrue(d.get("ticker_specific", False))
    def test_verification_status(self):
        from build_phase70_300394_curated_identity_patch import build
        r = build(); d = r["phase70_300394_curated_identity_patch"]
        if d["identity_patch_applied"]:
            self.assertEqual(d.get("verification_status"), "metadata_query_verified")
    def test_no_mock_fixture(self):
        from build_phase70_300394_curated_identity_patch import build
        r = build(); d = r["phase70_300394_curated_identity_patch"]
        self.assertFalse(d.get("mock_used",True)); self.assertFalse(d.get("fixture_used",True))
if __name__ == "__main__": unittest.main()
