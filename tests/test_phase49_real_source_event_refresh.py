import unittest
from phase49_helpers import make_phase49_conn
from run_phase49_real_source_event_refresh import build
class Phase49RefreshTests(unittest.TestCase):
    def test_dry_run(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ',mode='dry-run')
        r=p['real_source_event_refresh']; self.assertEqual(r['mode'],'dry-run'); self.assertFalse(r['audit_written'])
    def test_execute(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ',mode='execute')
        r=p['real_source_event_refresh']; self.assertTrue(r['audit_written']); self.assertGreater(r['events_refreshed'],0)
    def test_no_pending_order_trade(self):
        conn=make_phase49_conn(); p=build(conn,'300308.SZ',mode='execute')
        r=p['real_source_event_refresh']; self.assertEqual(r['pending_created'],0); self.assertEqual(r['paper_order_created'],0); self.assertEqual(r['real_trade_created'],0)
if __name__=='__main__': unittest.main()
