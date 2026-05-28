import unittest
from phase49_helpers import make_phase49_conn
from build_phase49_real_source_event_classifier import build
class Phase49ClassifierTests(unittest.TestCase):
    def test_classifies_sources(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ')
        c=p['real_source_event_classifier']; self.assertGreaterEqual(c['events_classified'],3)
    def test_ir_detected(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ')
        types=[r['event_type'] for r in p['real_source_event_classifier']['event_rows']]
        self.assertIn('investor_relations_record',types)
    def test_earnings_detected(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ')
        types=[r['event_type'] for r in p['real_source_event_classifier']['event_rows']]
        self.assertIn('earnings_report',types)
    def test_no_pending(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ')
        self.assertEqual(p['real_source_event_classifier']['pending_created'],0)
if __name__=='__main__': unittest.main()
