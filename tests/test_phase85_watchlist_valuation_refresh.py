import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestWatchlistRefresh(unittest.TestCase):
    def test_build(self):from build_phase85_watchlist_valuation_refresh import build;r=build();w=r["phase85_watchlist_valuation_refresh"];self.assertEqual(w["tickers_checked"],8)
    def test_no_pending(self):from build_phase85_watchlist_valuation_refresh import build;r=build();rows=r["phase85_watchlist_valuation_refresh"]["rows"];self.assertTrue(all(r["pending_created"]==0 for r in rows))
    def test_blocked_count(self):from build_phase85_watchlist_valuation_refresh import build;r=build();w=r["phase85_watchlist_valuation_refresh"];self.assertEqual(w["blocked_tickers"],1)
if __name__=="__main__":unittest.main()
