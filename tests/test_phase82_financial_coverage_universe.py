import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestUniverse(unittest.TestCase):
    def test_build(self):from smr_phase82_financial_coverage_universe import build_universe;r=build_universe();u=r["phase82_financial_coverage_universe"];self.assertGreater(u["tickers_total"],3)
    def test_markets(self):from smr_phase82_financial_coverage_universe import build_universe;r=build_universe();m=r["phase82_financial_coverage_universe"]["markets"];self.assertIn("CN_A",m)
    def test_300394_blocker(self):from smr_phase82_financial_coverage_universe import build_universe;r=build_universe();rows=r["phase82_financial_coverage_universe"]["rows"];row=[x for x in rows if x["ticker"]=="300394.SZ"];self.assertEqual(len(row),1);self.assertGreater(len(row[0]["expected_blockers"]),0)
if __name__=="__main__":unittest.main()
