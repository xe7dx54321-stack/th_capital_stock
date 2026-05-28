import phase52_helpers
import unittest; from build_phase52_next_event_watchlist import build
class Phase52NextEventTests(unittest.TestCase):
    def test_events(self):
        r=build(None,"300308.SZ"); n=r["next_event_watchlist"]
        self.assertGreaterEqual(len(n["events_to_watch"]),3)
    def test_monitoring_mode(self):
        r=build(None,"300308.SZ"); n=r["next_event_watchlist"]
        self.assertEqual(n["monitoring_mode"],"watchlist_tracking_only")
    def test_no_order_trigger(self):
        r=build(None,"300308.SZ"); n=r["next_event_watchlist"]
        for e in n["events_to_watch"]:
            self.assertNotEqual(e.get("expected_action"),"create_order")
if __name__=="__main__": unittest.main()
