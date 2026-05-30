import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestWatchlistIntel(unittest.TestCase):
    def test_build(self):from build_phase81_watchlist_time_series_intelligence_update import build;r=build();w=r["phase81_watchlist_time_series_intelligence_update"];self.assertGreater(w["tickers_checked"],0)
    def test_no_pending(self):from build_phase81_watchlist_time_series_intelligence_update import build;r=build();rows=r["phase81_watchlist_time_series_intelligence_update"]["rows"];self.assertTrue(all(row.get("pending_created",0)==0 and row.get("paper_order_created",0)==0 and row.get("real_trade_created",0)==0 for row in rows))
    def test_300394_blocker(self):from build_phase81_watchlist_time_series_intelligence_update import build;r=build();rows=[row for row in r["phase81_watchlist_time_series_intelligence_update"]["rows"] if row["ticker"]=="300394.SZ"];self.assertEqual(len(rows),1);self.assertIn("blocked",rows[0]["status"])
if __name__=="__main__":unittest.main()
