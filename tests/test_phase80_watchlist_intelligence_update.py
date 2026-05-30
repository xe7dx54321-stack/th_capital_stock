import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestWatchlist(unittest.TestCase):
    def test_build(self):from build_phase80_watchlist_intelligence_update import build;r=build();w=r["phase80_watchlist_intelligence_update"];self.assertGreater(w["tickers_checked"],0);self.assertGreaterEqual(w["updated_tickers"],0)
    def test_no_pending(self):from build_phase80_watchlist_intelligence_update import build;r=build();w=r["phase80_watchlist_intelligence_update"];self.assertTrue(all(row.get("pending_created",0)==0 and row.get("paper_order_created",0)==0 and row.get("real_trade_created",0)==0 for row in w["rows"]))
    def test_688041_has_signal(self):from build_phase80_watchlist_intelligence_update import build;r=build();rows=[row for row in r["phase80_watchlist_intelligence_update"]["rows"] if row["ticker"]=="688041.SH"];self.assertEqual(len(rows),1);self.assertGreaterEqual(rows[0].get("new_time_series_signal_count",0),0)
    def test_300394_blocker(self):from build_phase80_watchlist_intelligence_update import build;r=build();rows=[row for row in r["phase80_watchlist_intelligence_update"]["rows"] if row["ticker"]=="300394.SZ"];self.assertEqual(len(rows),1);self.assertIn("blocked",rows[0]["status"])
    def test_no_mock(self):from build_phase80_watchlist_intelligence_update import build;r=build();self.assertFalse(r["phase80_watchlist_intelligence_update"]["mock_used"]);self.assertFalse(r["phase80_watchlist_intelligence_update"]["fixture_used"])
if __name__=="__main__":unittest.main()
