import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestDashboard(unittest.TestCase):
    def test_build(self):from build_phase83_hk_us_financial_adapter_dashboard import build;r=build();s=r["summary"];self.assertGreater(s["tickers_checked"],0)
    def test_markets(self):from build_phase83_hk_us_financial_adapter_dashboard import build;r=build();s=r["summary"];self.assertGreater(s["hk_tickers_checked"],0);self.assertGreater(s["us_tickers_checked"],0)
    def test_no_pending(self):from build_phase83_hk_us_financial_adapter_dashboard import build;r=build();s=r["summary"];self.assertEqual(s["pending_created"],0)
    def test_no_mock(self):from build_phase83_hk_us_financial_adapter_dashboard import build;r=build();s=r["summary"];self.assertFalse(s["mock_used"])
    def test_covered_after(self):from build_phase83_hk_us_financial_adapter_dashboard import build;r=build();s=r["summary"];self.assertGreaterEqual(s["covered_after_phase83"],s["covered_before_phase83"])
if __name__=="__main__":unittest.main()
