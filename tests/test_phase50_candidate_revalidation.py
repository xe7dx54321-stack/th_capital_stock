import unittest; from phase50_helpers import make_phase50_conn; from validate_phase50_real_source_candidate_revalidation import build
class Phase50RevalidationTests(unittest.TestCase):
    def test_revalidation_pass(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); r=p['real_source_candidate_revalidation']; self.assertEqual(r['overall_status'],'pass')
    def test_sensitive_not_confirmed(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); r=p['real_source_candidate_revalidation']; self.assertFalse(r['official_consensus_confirmed']); self.assertFalse(r['supplier_share_confirmed']); self.assertFalse(r['customer_allocation_confirmed'])
    def test_no_pending(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); r=p['real_source_candidate_revalidation']; self.assertEqual(r['pending_created'],0); self.assertEqual(r['paper_order_created'],0); self.assertEqual(r['real_trade_created'],0)
if __name__=='__main__': unittest.main()
