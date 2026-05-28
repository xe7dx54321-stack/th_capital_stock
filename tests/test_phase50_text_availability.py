import unittest; from phase50_helpers import make_phase50_conn; from build_phase50_real_source_text_availability import build
class Phase50TextAvailabilityTests(unittest.TestCase):
    def test_sources_checked(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); a=p['real_source_text_availability']; self.assertGreater(a['sources_checked'],0)
    def test_text_available(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); a=p['real_source_text_availability']; self.assertGreater(a.get('text_available',0),0)
    def test_metadata_not_evidence(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); self.assertEqual(p['real_source_text_availability']['pending_created'],0)
    def test_no_pending(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); self.assertEqual(p['real_source_text_availability']['paper_order_created'],0)
if __name__=='__main__': unittest.main()
