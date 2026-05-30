import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestUniverse(unittest.TestCase):
    def test_build(self):from build_phase84_daily_monitoring_universe import build;r=build();u=r["phase84_daily_monitoring_universe"];self.assertEqual(u["tickers_total"],8)
    def test_daily_enabled(self):from build_phase84_daily_monitoring_universe import build;r=build();u=r["phase84_daily_monitoring_universe"];self.assertEqual(u["daily_monitoring_enabled"],7)
    def test_blocked(self):from build_phase84_daily_monitoring_universe import build;r=build();u=r["phase84_daily_monitoring_universe"];self.assertEqual(u["blocked"],1)
    def test_300394_blocked(self):from build_phase84_daily_monitoring_universe import build;r=build();rows=r["phase84_daily_monitoring_universe"]["rows"];r394=[r for r in rows if r["ticker"]=="300394.SZ"][0];self.assertTrue(r394["blocked"])
    def test_markets(self):from build_phase84_daily_monitoring_universe import build;r=build();m=r["phase84_daily_monitoring_universe"]["markets"];self.assertIn("CN_A",m);self.assertIn("HK",m);self.assertIn("US",m)
if __name__=="__main__":unittest.main()
