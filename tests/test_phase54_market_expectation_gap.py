import phase54_helpers, unittest; from smr_market_expectation_gap_checker import build_gap_report, check_market_gap
class Phase54MarketGapTests(unittest.TestCase):
    def test_gap_present(self):
        r=check_market_gap()
        self.assertIn("expectation_gap_status",r)
    def test_not_confirmed(self):
        r=check_market_gap()
        self.assertEqual(r["consensus_source_status"],"not_authoritatively_confirmed")
    def test_confirm_disprove(self):
        r=check_market_gap()
        self.assertGreater(len(r["what_would_confirm_gap"]),0)
        self.assertGreater(len(r["what_would_disprove_gap"]),0)
if __name__=="__main__": unittest.main()
