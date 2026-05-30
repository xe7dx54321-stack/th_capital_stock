import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBrief(unittest.TestCase):
    def test_build(self):
        from build_phase79_internal_brief import build
        r=build();b=r["phase79_internal_brief"]
        self.assertEqual(b["tickers_covered"],3)
    def test_has_boss_summary(self):
        from build_phase79_internal_brief import build
        r=build();b=r["phase79_internal_brief"]
        self.assertIn("Boss Summary",b["markdown"])
    def test_no_trade(self):
        from build_phase79_internal_brief import build
        r=build();b=r["phase79_internal_brief"]
        self.assertNotIn("买入",b["markdown"])
        self.assertNotIn("卖出",b["markdown"])
        self.assertNotIn("目标价",b["markdown"])
if __name__=="__main__":unittest.main()
