import unittest
from phase49_helpers import make_phase49_conn
from run_phase49_cninfo_source_metadata_scan import build_scan_result
class Phase49CNINFOConnectorTests(unittest.TestCase):
    def test_skip_network_works(self):
        conn=make_phase49_conn(); p=build_scan_result(conn,'300308.SZ',mode='dry-run',skip_network=True)
        s=p['cninfo_source_metadata_scan']; self.assertFalse(s['network_used']); self.assertTrue(s['fallback_used'])
        self.assertGreater(s['sources_found'],0)
    def test_metadata_only(self):
        conn=make_phase49_conn(); p=build_scan_result(conn,'300308.SZ',mode='dry-run',skip_network=True)
        s=p['cninfo_source_metadata_scan']; self.assertTrue(s['metadata_only']); self.assertFalse(s['raw_content_saved'])
    def test_no_pending(self):
        conn=make_phase49_conn(); p=build_scan_result(conn,'300308.SZ',mode='dry-run',skip_network=True)
        s=p['cninfo_source_metadata_scan']; self.assertEqual(s['pending_created'],0)
if __name__=='__main__': unittest.main()
