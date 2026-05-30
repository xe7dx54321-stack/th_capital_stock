import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestWatchBoard(unittest.TestCase):
    def test_build(self):from build_phase84_portfolio_watch_board import build;r=build();b=r["phase84_portfolio_watch_board"];self.assertEqual(b["tickers_total"],8)
    def test_five_sections(self):from build_phase84_portfolio_watch_board import build;r=build();b=r["phase84_portfolio_watch_board"];self.assertEqual(len(b["sections"]),5)
    def test_blocked_section(self):from build_phase84_portfolio_watch_board import build;r=build();b=r["phase84_portfolio_watch_board"];self.assertIn("blocked",b["sections"])
    def test_no_pending(self):from build_phase84_portfolio_watch_board import build;r=build();rows=r["phase84_portfolio_watch_board"]["rows"];self.assertTrue(all(row["pending_created"]==0 for row in rows))
if __name__=="__main__":unittest.main()
