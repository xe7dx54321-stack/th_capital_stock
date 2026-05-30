import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBlockerRefresh(unittest.TestCase):
    def test_build(self):from build_phase84_daily_coverage_blocker_refresh import build;r=build();b=r["phase84_daily_coverage_blocker_refresh"];self.assertEqual(b["blocked_tickers"],1)
    def test_300394(self):from build_phase84_daily_coverage_blocker_refresh import build;r=build();rows=r["phase84_daily_coverage_blocker_refresh"]["rows"];self.assertEqual(rows[0]["ticker"],"300394.SZ")
    def test_has_next_action(self):from build_phase84_daily_coverage_blocker_refresh import build;r=build();rows=r["phase84_daily_coverage_blocker_refresh"]["rows"];self.assertTrue(len(rows[0]["allowed_next_action"])>0)
if __name__=="__main__":unittest.main()
