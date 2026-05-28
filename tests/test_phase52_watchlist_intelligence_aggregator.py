import phase52_helpers
import unittest; from smr_watchlist_intelligence_aggregator import aggregate_intelligence
class Phase52AggregatorTests(unittest.TestCase):
    def test_aggregator_output(self):
        r=aggregate_intelligence("300308.SZ"); a=r["watchlist_intelligence_aggregator"]
        self.assertEqual(a["current_watchlist_status"],"tracking_strengthened")
    def test_no_pending(self):
        r=aggregate_intelligence("300308.SZ"); a=r["watchlist_intelligence_aggregator"]
        self.assertFalse(a["pending_allowed"]); self.assertFalse(a["paper_order_allowed"])
    def test_phases_covered(self):
        r=aggregate_intelligence("300308.SZ"); a=r["watchlist_intelligence_aggregator"]
        for k in ["phase45_research_status","phase46_watchlist_entry"]: self.assertIn(k,a)
if __name__=="__main__": unittest.main()
