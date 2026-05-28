import unittest
from phase49_helpers import make_phase49_conn
from build_phase49_metadata_watchlist_events import build
class Phase49AdapterTests(unittest.TestCase):
    def test_adapts_events(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ')
        a=p['metadata_watchlist_events']; self.assertGreaterEqual(a['watchlist_events_created'],3)
    def test_forbidden_actions(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ')
        for e in p['metadata_watchlist_events']['events']:
            self.assertIn('create_pending',e.get('forbidden_actions')or[])
    def test_no_pending(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ')
        self.assertEqual(p['metadata_watchlist_events']['pending_created'],0)
if __name__=='__main__': unittest.main()
