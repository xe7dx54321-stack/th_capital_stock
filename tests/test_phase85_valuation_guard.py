import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestValuationGuard(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_guard_report import build;r=build();g=r["phase85_valuation_guard"];self.assertEqual(g["overall_status"],"pass")
    def test_no_low_as_buy(self):from build_phase85_valuation_guard_report import build;r=build();g=r["phase85_valuation_guard"];self.assertTrue(g["checks"]["no_low_as_buy"])
    def test_no_high_as_sell(self):from build_phase85_valuation_guard_report import build;r=build();g=r["phase85_valuation_guard"];self.assertTrue(g["checks"]["no_high_as_sell"])
    def test_watch_only(self):from build_phase85_valuation_guard_report import build;r=build();g=r["phase85_valuation_guard"];self.assertTrue(g["checks"]["watch_only"])
if __name__=="__main__":unittest.main()
