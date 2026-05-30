import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestWatchlist(unittest.TestCase):
    def test_build(self):from build_phase82_multi_ticker_watchlist_intelligence_update import build;r=build();w=r["phase82_multi_ticker_watchlist_intelligence_update"];self.assertGreater(w["tickers_checked"],0)
    def test_no_pending(self):from build_phase82_multi_ticker_watchlist_intelligence_update import build;r=build();rows=r["phase82_multi_ticker_watchlist_intelligence_update"]["rows"];self.assertTrue(all(row.get("pending_created",0)==0 and row.get("paper_order_created",0)==0 and row.get("real_trade_created",0)==0 for row in rows))
    def test_updated_and_blocked(self):from build_phase82_multi_ticker_watchlist_intelligence_update import build;r=build();w=r["phase82_multi_ticker_watchlist_intelligence_update"];self.assertGreaterEqual(w["updated_tickers"],0);self.assertGreaterEqual(w["blocked_tickers"],0)
if __name__=="__main__":unittest.main()
