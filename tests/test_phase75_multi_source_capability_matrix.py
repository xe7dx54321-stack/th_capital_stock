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
    def test_link_not_text(self):
        from build_phase75_multi_source_capability_matrix import build
        r = build()
        for row in r["phase75_multi_source_capability_matrix"]["rows"]:
            if "sse_html" in row:
                self.assertNotEqual(row.get("sse_html"), "text_available")
    def test_text_not_evidence(self):
        from build_phase75_multi_source_capability_matrix import build
        r = build()
        for row in r["phase75_multi_source_capability_matrix"]["rows"]:
            if "irm_html" in row:
                self.assertNotEqual(row.get("irm_html"), "evidence_available")

if __name__ == "__main__":
    unittest.main()
