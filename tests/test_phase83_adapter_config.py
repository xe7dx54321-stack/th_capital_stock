import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestConfig(unittest.TestCase):
    def test_load(self):from smr_phase83_adapter_config import load_config;c=load_config();self.assertIn("hk_us",c["strategy"])
    def test_validate(self):from smr_phase83_adapter_config import validate_config;v=validate_config();self.assertTrue(v["all_pass"])
    def test_has_hk_us(self):from smr_phase83_adapter_config import load_config;c=load_config();ts=c["target_tickers"];self.assertTrue(any(t["ticker"]=="09988.HK"for t in ts));self.assertTrue(any(t["ticker"]=="NVDA"for t in ts))
if __name__=="__main__":unittest.main()
