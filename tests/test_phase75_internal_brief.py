import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestPhase75InternalBrief(unittest.TestCase):
    def test_build(self):
        from build_phase75_internal_brief import build
        r = build()
        br = r["phase75_internal_brief"]
        self.assertEqual(br["sections"], 5)
    def test_has_boss_summary(self):
        from build_phase75_internal_brief import build
        r = build()
        md = r["phase75_internal_brief"]["markdown"]
        self.assertTrue("Boss Summary" in md or "老板摘要" in md)
    def test_no_system_terms(self):
        from build_phase75_internal_brief import build
        r = build()
        md = r["phase75_internal_brief"]["markdown"]
        self.assertNotIn("pipeline", md.lower())
        self.assertNotIn("dashboard", md.lower())
        self.assertNotIn("runner", md.lower())
    def test_no_trade_terms(self):
        from build_phase75_internal_brief import build
        r = build()
        md = r["phase75_internal_brief"]["markdown"]
        self.assertNotIn("buy", md.lower())
        self.assertNotIn("sell", md.lower())

if __name__ == "__main__":
    unittest.main()
