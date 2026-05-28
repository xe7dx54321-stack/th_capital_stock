import unittest
from phase49_helpers import make_phase49_conn
from build_phase49_event_dedup_report import build
class Phase49DedupTests(unittest.TestCase):
    def test_dedup_report(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ')
        d=p['event_dedup_report']; self.assertGreater(d['events_checked'],0)
    def test_no_duplicates_with_unique_sources(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ')
        d=p['event_dedup_report']; self.assertEqual(d['duplicates_skipped'],0)
if __name__=='__main__': unittest.main()
