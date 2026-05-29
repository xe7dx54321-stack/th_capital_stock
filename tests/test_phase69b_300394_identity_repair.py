import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
for p in [str(L), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)

class Test300394IdentityRepair(unittest.TestCase):
    def test_identity_repair_attempted(self):
        from smr_phase69b_cninfo_identity_repair import attempt_identity_repair
        r = attempt_identity_repair('300394.SZ')
        self.assertTrue(r['identity_repair_attempted'])

    def test_no_reuse_300308_org_id(self):
        from smr_phase69b_cninfo_identity_repair import attempt_identity_repair
        from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
        r = attempt_identity_repair('300394.SZ')
        if r.get('identity_found'):
            org308 = CURATED_CNINFO_IDENTITIES.get('300308.SZ', {}).get('org_id', '')
            self.assertNotEqual(r.get('org_id'), org308)

    def test_unverified_not_marked_verified(self):
        from smr_phase69b_cninfo_identity_repair import attempt_identity_repair
        r = attempt_identity_repair('300394.SZ')
        if not r['identity_found']:
            self.assertNotEqual(r.get('identity_confidence'), 'verified')

    def test_failure_has_reason(self):
        from smr_phase69b_cninfo_identity_repair import attempt_identity_repair
        r = attempt_identity_repair('300394.SZ')
        if not r['identity_found']:
            self.assertIsNotNone(r.get('failure_reason'))
            self.assertIsNotNone(r.get('next_action'))

    def test_no_mock_fixture(self):
        from smr_phase69b_cninfo_identity_repair import attempt_identity_repair
        r = attempt_identity_repair('300394.SZ')
        self.assertFalse(r.get('mock_used', True))
        self.assertFalse(r.get('fixture_used', True))

    def test_report_outputs(self):
        from build_phase69b_300394_identity_repair import build
        r = build()
        self.assertIsNotNone(r)
        self.assertIn('300394', str(r))

if __name__ == '__main__': unittest.main()
