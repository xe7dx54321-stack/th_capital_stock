import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestWatchlistIntelligence(unittest.TestCase):
    def test_build(self):
        from build_phase78_watchlist_intelligence_update import build
        r=build();w=r["phase78_watchlist_intelligence_update"]
        self.assertGreater(w["updated_tickers"],0)
    def test_no_pending_order(self):
        from build_phase78_watchlist_intelligence_update import build
        r=build();rows=r["phase78_watchlist_intelligence_update"]["rows"]
        for row in rows:
            if "pending_created" in row:
                self.assertEqual(row["pending_created"],0)
                self.assertEqual(row["paper_order_created"],0)
                self.assertEqual(row["real_trade_created"],0)
    def test_300394_blocker(self):
        from build_phase78_watchlist_intelligence_update import build
        r=build();rows=r["phase78_watchlist_intelligence_update"]["rows"]
        f394=[r for r in rows if r["ticker"]=="300394.SZ"]
        self.assertEqual(len(f394),1)
        self.assertIn("blocker",f394[0]["watchlist_decision"])
if __name__=="__main__":unittest.main()
