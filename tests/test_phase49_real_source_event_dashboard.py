import unittest
from phase49_helpers import make_phase49_active_conn
from build_phase49_real_source_event_dashboard import build
class Phase49DashboardTests(unittest.TestCase):
    def test_dashboard(self):
        conn=make_phase49_active_conn(); p=build(conn,'300308.SZ')
        s=p['summary']; self.assertGreater(s['sources_found'],0); self.assertGreater(s['watchlist_events_created'],0)
        self.assertEqual(s['pending_created'],0); self.assertEqual(s['paper_order_created'],0); self.assertEqual(s['real_trade_created'],0)
    def test_breakdowns(self):
        conn=make_phase49_active_conn(); p=build(conn,'300308.SZ')
        self.assertIn('cninfo_investor_relations',p.get('source_type_breakdown')or{})
        self.assertIn('investor_relations_record',p.get('event_type_breakdown')or{})
if __name__=='__main__': unittest.main()
