import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestPhase75MultiSourceMatrix(unittest.TestCase):
    def test_build(self):
        from build_phase75_multi_source_capability_matrix import build
        r = build()
        m = r["phase75_multi_source_capability_matrix"]
        self.assertEqual(m["tickers_checked"], 3)
        self.assertEqual(m["tickers_with_fallback_text"], 0)
    def test_blockers_present(self):
        from build_phase75_multi_source_capability_matrix import build
        r = build()
        for row in r["phase75_multi_source_capability_matrix"]["rows"]:
            if row["overall"] != "full_chain_available":
                self.assertIn("blocker", row)

if __name__ == "__main__":
    unittest.main()
