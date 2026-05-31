import unittest, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase91_ticker_source_profile import build_ticker_source_profiles

class TestProfiles(unittest.TestCase):
    def test_8_tickers(self):
        result=build_ticker_source_profiles()
        self.assertEqual(result["phase91_ticker_source_profile"]["tickers_profiled"],8)
    def test_nvda_highest(self):
        result=build_ticker_source_profiles()
        nvda=[p for p in result["phase91_ticker_source_profile"]["profiles"] if p["ticker"]=="NVDA"][0]
        self.assertGreaterEqual(nvda["source_depth_score"],7)
    def test_300394_blocked(self):
        result=build_ticker_source_profiles()
        p394=[p for p in result["phase91_ticker_source_profile"]["profiles"] if p["ticker"]=="300394.SZ"][0]
        self.assertTrue(p394["blocked"])
        self.assertEqual(p394["source_depth_score"],0)
    def test_688041_gaps(self):
        result=build_ticker_source_profiles()
        p=[p for p in result["phase91_ticker_source_profile"]["profiles"] if p["ticker"]=="688041.SH"][0]
        self.assertIn("pricing_unavailable",p.get("hard_data_gaps",[]))
    def test_markets_present(self):
        result=build_ticker_source_profiles()
        markets=set(p["market"] for p in result["phase91_ticker_source_profile"]["profiles"])
        self.assertIn("CN_A",markets)
        self.assertIn("HK",markets)
        self.assertIn("US",markets)
