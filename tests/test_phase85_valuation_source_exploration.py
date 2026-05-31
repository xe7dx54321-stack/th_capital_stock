import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestSourceExploration(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_source_exploration import build;r=build();s=r["phase85_valuation_source_exploration"];self.assertGreater(s["source_attempted_total"],0)
    def test_tickers_with_source(self):from build_phase85_valuation_source_exploration import build;r=build();s=r["phase85_valuation_source_exploration"];self.assertGreaterEqual(s["ticker_with_selected_source"],0)
    def test_300394_blocked(self):from build_phase85_valuation_source_exploration import build;r=build();rows=r["phase85_valuation_source_exploration"]["rows"];r394=[r for r in rows if r["ticker"]=="300394.SZ"][0];self.assertTrue(r394["blocked"])
if __name__=="__main__":unittest.main()
