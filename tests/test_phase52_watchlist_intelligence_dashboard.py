import phase52_helpers
import unittest; from build_phase52_watchlist_intelligence_dashboard import build
class Phase52DashboardTests(unittest.TestCase):
    def test_dashboard(self):
        r=build(None,"300308.SZ"); s=r["summary"]
        self.assertEqual(s["tracking_decision"],"continue_tracking")
    def test_no_pending(self):
        r=build(None,"300308.SZ"); s=r["summary"]
        self.assertEqual(s["pending_created"],0)
        self.assertEqual(s["paper_order_created"],0)
    def test_scores(self):
        r=build(None,"300308.SZ"); s=r["summary"]
        self.assertGreaterEqual(s["tracking_support_candidates"],1)
if __name__=="__main__": unittest.main()
