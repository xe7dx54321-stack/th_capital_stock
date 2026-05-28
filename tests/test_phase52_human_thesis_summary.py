import phase52_helpers
import unittest; from smr_human_readable_thesis_summary import build_thesis_summary
class Phase52ThesisSummaryTests(unittest.TestCase):
    def test_summary_output(self):
        r=build_thesis_summary("300308.SZ"); h=r["human_thesis_summary"]
        self.assertIn("positive_watchlist",h["current_thesis_status"])
    def test_no_buy_signal(self):
        r=build_thesis_summary("300308.SZ"); h=r["human_thesis_summary"]
        self.assertIn("buy_signal",h["forbidden_interpretation"])
    def test_why_not_pending(self):
        r=build_thesis_summary("300308.SZ"); h=r["human_thesis_summary"]
        self.assertGreater(len(h["why_not_pending"]),0)
if __name__=="__main__": unittest.main()
