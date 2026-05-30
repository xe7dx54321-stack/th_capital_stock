import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestWatchlistRefresh(unittest.TestCase):
    def test_build(self):from build_phase84_watchlist_daily_refresh import build;r=build();w=r["phase84_watchlist_daily_refresh"];self.assertEqual(w["tickers_checked"],8)
    def test_no_pending(self):from build_phase84_watchlist_daily_refresh import build;r=build();rows=r["phase84_watchlist_daily_refresh"]["rows"];self.assertTrue(all(row["pending_created"]==0 for row in rows))
    def test_no_trade(self):from build_phase84_watchlist_daily_refresh import build;r=build();rows=r["phase84_watchlist_daily_refresh"]["rows"];self.assertTrue(all(row["real_trade_created"]==0 for row in rows))
    def test_blocked_count(self):from build_phase84_watchlist_daily_refresh import build;r=build();w=r["phase84_watchlist_daily_refresh"];self.assertEqual(w["blocked_tickers"],1)
if __name__=="__main__":unittest.main()
