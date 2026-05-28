import unittest; from phase50_helpers import make_phase50_conn; from build_phase50_real_source_candidate_review_queue import build
class Phase50ReviewQueueTests(unittest.TestCase):
    def test_queue_items(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); q=p['real_source_candidate_review_queue']; self.assertGreater(q['queue_items'],0)
    def test_forbidden_actions(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); fa=p['real_source_candidate_review_queue']['forbidden_actions']; self.assertIn('create_pending',fa); self.assertIn('create_order',fa)
if __name__=='__main__': unittest.main()
