import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestWatchlistIntelligence(unittest.TestCase):
    def test_build(self):
        from build_phase77_watchlist_intelligence_update import build
        r=build();wu=r["phase77_watchlist_intelligence_update"]
        self.assertEqual(wu["tickers_checked"],3)
    def test_no_pending_order(self):
        from build_phase77_watchlist_intelligence_update import build
        r=build()
        for row in r["phase77_watchlist_intelligence_update"]["rows"]:
            if "pending_created" in row:
                self.assertEqual(row["pending_created"],0)
if __name__=="__main__":unittest.main()
