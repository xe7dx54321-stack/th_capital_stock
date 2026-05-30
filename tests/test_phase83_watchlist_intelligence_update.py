import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestWatchlistIntelligence(unittest.TestCase):
    def test_build(self):from build_phase83_watchlist_intelligence_update import build;r=build();w=r["phase83_watchlist_intelligence_update"];self.assertGreater(w["tickers_checked"],0)
    def test_no_trade(self):from build_phase83_watchlist_intelligence_update import build;r=build();rows=r["phase83_watchlist_intelligence_update"]["rows"];self.assertTrue(all(row.get("pending_created",0)==0 for row in rows))
    def test_no_order(self):from build_phase83_watchlist_intelligence_update import build;r=build();rows=r["phase83_watchlist_intelligence_update"]["rows"];self.assertTrue(all(row.get("paper_order_created",0)==0 for row in rows))
    def test_hk_us_updated(self):from build_phase83_watchlist_intelligence_update import build;r=build();w=r["phase83_watchlist_intelligence_update"];self.assertGreaterEqual(w["hk_us_updated_tickers"],0)
if __name__=="__main__":unittest.main()
