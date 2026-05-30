import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBrief(unittest.TestCase):
    def test_build(self):
        from build_phase77_internal_brief import build
        r=build();br=r["phase77_internal_brief"]
        self.assertEqual(br["sections"],5)
    def test_has_boss_summary(self):
        from build_phase77_internal_brief import build
        r=build();md=r["phase77_internal_brief"]["markdown"]
        self.assertIn("Boss Summary",md)
    def test_no_trade(self):
        from build_phase77_internal_brief import build
        r=build();md=r["phase77_internal_brief"]["markdown"]
        self.assertNotIn("buy",md.lower());self.assertNotIn("sell",md.lower())
if __name__=="__main__":unittest.main()
