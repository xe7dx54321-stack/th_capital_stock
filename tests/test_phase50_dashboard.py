import unittest; from phase50_helpers import make_phase50_conn; from build_phase50_real_source_text_evidence_dashboard import build
class Phase50DashboardTests(unittest.TestCase):
    def test_dashboard(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); s=p['summary']; self.assertGreater(s['text_extracted'],0); self.assertGreater(s['chunks_created'],0)
    def test_no_pending(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); s=p['summary']; self.assertEqual(s['pending_created'],0); self.assertEqual(s['paper_order_created'],0); self.assertEqual(s['real_trade_created'],0); self.assertEqual(s['promotion_allowed_true'],0)
if __name__=='__main__': unittest.main()
