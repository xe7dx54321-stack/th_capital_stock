import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestConfig(unittest.TestCase):
    def test_load(self):from smr_phase82_coverage_config import load_config;c=load_config();self.assertIn("multi_ticker",c["strategy"])
    def test_validate(self):from smr_phase82_coverage_config import validate_config;v=validate_config();self.assertTrue(v["all_pass"])
    def test_has_universe(self):from smr_phase82_coverage_config import load_config;c=load_config();self.assertGreater(len(c["universe"]),3)
    def test_has_002230(self):from smr_phase82_coverage_config import load_config;c=load_config();self.assertTrue(any(t["ticker"]=="002230.SZ" for t in c["universe"]))
    def test_markets(self):from smr_phase82_coverage_config import load_config;c=load_config();markets=set(t["market"] for t in c["universe"]);self.assertIn("CN_A",markets)
if __name__=="__main__":unittest.main()
