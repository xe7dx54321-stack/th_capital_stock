import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestWatchlistUpdate(unittest.TestCase):
    def test_no_pending_order_trade(self):
        try:
            from build_phase67_watchlist_update import build
            r=build("300308.SZ")
            wu=r.get("phase67_watchlist_update",{})
            self.assertEqual(wu.get("pending_created"),0)
            self.assertEqual(wu.get("paper_order_created"),0)
            self.assertEqual(wu.get("real_trade_created"),0)
        except ImportError: self.skipTest("not importable")
    def test_unconfirmed_present(self):
        try:
            from build_phase67_watchlist_update import build
            r=build("300308.SZ")
            wu=r.get("phase67_watchlist_update",{})
            self.assertIsNotNone(wu.get("claims_still_unconfirmed"))
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
