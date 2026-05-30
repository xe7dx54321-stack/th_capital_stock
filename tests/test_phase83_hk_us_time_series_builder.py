import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestTimeSeries(unittest.TestCase):
    def test_build(self):from smr_phase83_hk_us_time_series_builder import build_hk_us_time_series;r=build_hk_us_time_series();ts=r["phase83_hk_us_time_series_signal"];self.assertGreater(ts["signals_created"],0)
    def test_cannot_conclude(self):from smr_phase83_hk_us_time_series_builder import build_hk_us_time_series;r=build_hk_us_time_series();rows=r["phase83_hk_us_time_series_signal"]["rows"];self.assertTrue(all(len(row["cannot_conclude"])>0 for row in rows))
    def test_markets(self):from smr_phase83_hk_us_time_series_builder import build_hk_us_time_series;r=build_hk_us_time_series();markets=set(row["market"]for row in r["phase83_hk_us_time_series_signal"]["rows"]);self.assertTrue({"HK","US"}.issubset(markets)or len(markets.intersection({"HK","US"}))>0)
if __name__=="__main__":unittest.main()
