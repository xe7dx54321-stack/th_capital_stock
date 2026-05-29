import unittest,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path: sys.path.insert(0,str(R))
class TestWatchlist(unittest.TestCase):
    def test_no_pending_order_trade(self):
        try:
            from build_phase67b_watchlist_update import build
            r=build("300308.SZ");wu=r["phase67b_watchlist_update"]
            self.assertEqual(wu["pending_created"],0);self.assertEqual(wu["paper_order_created"],0);self.assertEqual(wu["real_trade_created"],0)
        except ImportError: self.skipTest("not importable")
    def test_unconfirmed_present(self):
        try:
            from build_phase67b_watchlist_update import build
            r=build("300308.SZ")
            self.assertIsNotNone(r["phase67b_watchlist_update"]["claims_still_unconfirmed"])
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
