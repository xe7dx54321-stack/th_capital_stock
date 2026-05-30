import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestDashboard(unittest.TestCase):
    def test_build(self):from build_phase82_multi_ticker_financial_monitoring_dashboard import build;r=build();s=r["summary"];self.assertGreater(s["tickers_checked"],0)
    def test_markets(self):from build_phase82_multi_ticker_financial_monitoring_dashboard import build;r=build();s=r["summary"];self.assertIn("CN_A",s["markets"])
    def test_no_pending(self):from build_phase82_multi_ticker_financial_monitoring_dashboard import build;r=build();s=r["summary"];self.assertEqual(s["pending_created"],0)
    def test_no_mock(self):from build_phase82_multi_ticker_financial_monitoring_dashboard import build;r=build();s=r["summary"];self.assertFalse(s["mock_used"])
    def test_claims(self):from build_phase82_multi_ticker_financial_monitoring_dashboard import build;r=build();s=r["summary"];self.assertGreaterEqual(s["tickers_with_signals"],0)
if __name__=="__main__":unittest.main()
