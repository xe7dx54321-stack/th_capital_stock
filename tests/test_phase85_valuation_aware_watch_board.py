import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestWatchBoard(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_aware_watch_board import build;r=build();b=r["phase85_valuation_aware_watch_board"];self.assertEqual(b["tickers_total"],8)
    def test_sections(self):from build_phase85_valuation_aware_watch_board import build;r=build();b=r["phase85_valuation_aware_watch_board"];self.assertGreater(len(b["sections"]),0)
    def test_no_pending(self):from build_phase85_valuation_aware_watch_board import build;r=build();rows=r["phase85_valuation_aware_watch_board"]["rows"];self.assertTrue(all(row["pending_created"]==0 for row in rows))
    def test_no_target_price(self):from build_phase85_valuation_aware_watch_board import build;r=build();rows=r["phase85_valuation_aware_watch_board"]["rows"];self.assertTrue(all(row["target_price"] is None for row in rows))
if __name__=="__main__":unittest.main()
