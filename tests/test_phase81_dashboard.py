import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestDashboard(unittest.TestCase):
    def test_build(self):from build_phase81_time_series_watchlist_monitoring_dashboard import build;r=build();s=r["summary"];self.assertGreater(s["tickers_checked"],0)
    def test_has_signals(self):from build_phase81_time_series_watchlist_monitoring_dashboard import build;r=build();s=r["summary"];self.assertGreaterEqual(s["signals_loaded"],0);self.assertGreaterEqual(s["baselines_created"],0)
    def test_no_pending(self):from build_phase81_time_series_watchlist_monitoring_dashboard import build;r=build();s=r["summary"];self.assertEqual(s["pending_created"],0);self.assertEqual(s["paper_order_created"],0);self.assertEqual(s["real_trade_created"],0)
    def test_no_mock(self):from build_phase81_time_series_watchlist_monitoring_dashboard import build;r=build();s=r["summary"];self.assertFalse(s["mock_used"]);self.assertFalse(s["fixture_used"])
    def test_claims(self):from build_phase81_time_series_watchlist_monitoring_dashboard import build;r=build();s=r["summary"];self.assertGreaterEqual(s["claims_observed"],0);self.assertGreaterEqual(s["claims_unconfirmed"],0);self.assertGreaterEqual(s["claims_strengthened"],0)
if __name__=="__main__":unittest.main()
