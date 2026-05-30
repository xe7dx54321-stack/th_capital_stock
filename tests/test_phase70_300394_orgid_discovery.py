import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
for p in [str(L), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)
class Test300394OrgIdDiscovery(unittest.TestCase):
    def test_discovery_attempted(self):
        from build_phase70_300394_orgid_discovery import build
        r = build(); d = r["phase70_300394_orgid_discovery"]
        self.assertTrue(d["discovery_attempted"])
    def test_no_reuse_300308_org_id(self):
        from build_phase70_300394_orgid_discovery import build
        from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
        r = build(); d = r["phase70_300394_orgid_discovery"]
        if d.get("verified_org_id_found"):
            org308 = CURATED_CNINFO_IDENTITIES.get("300308.SZ",{}).get("org_id","")
            self.assertNotEqual(d.get("org_id"), org308)
    def test_candidates_tested(self):
        from build_phase70_300394_orgid_discovery import build
        r = build(); d = r["phase70_300394_orgid_discovery"]
        self.assertGreater(d["candidates_tested"], 0)
    def test_failure_has_action(self):
        from build_phase70_300394_orgid_discovery import build
        r = build(); d = r["phase70_300394_orgid_discovery"]
        if not d["verified_org_id_found"]:
            self.assertIn("next_manual_action", d)
    def test_no_mock_fixture(self):
        from build_phase70_300394_orgid_discovery import build
        r = build(); d = r["phase70_300394_orgid_discovery"]
        self.assertFalse(d.get("mock_used",True)); self.assertFalse(d.get("fixture_used",True))
if __name__ == "__main__": unittest.main()
