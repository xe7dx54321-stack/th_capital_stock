import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestDashboard(unittest.TestCase):
    def test_build(self):from build_phase84_scheduled_daily_monitoring_dashboard import build;r=build();s=r["summary"];self.assertGreater(s["tickers_total"],0)
    def test_daily_monitoring(self):from build_phase84_scheduled_daily_monitoring_dashboard import build;r=build();s=r["summary"];self.assertEqual(s["daily_monitoring_enabled"],7)
    def test_no_pending(self):from build_phase84_scheduled_daily_monitoring_dashboard import build;r=build();s=r["summary"];self.assertEqual(s["pending_created"],0)
    def test_no_mock(self):from build_phase84_scheduled_daily_monitoring_dashboard import build;r=build();s=r["summary"];self.assertFalse(s["mock_used"])
    def test_no_order(self):from build_phase84_scheduled_daily_monitoring_dashboard import build;r=build();s=r["summary"];self.assertEqual(s["paper_order_created"],0)
if __name__=="__main__":unittest.main()
