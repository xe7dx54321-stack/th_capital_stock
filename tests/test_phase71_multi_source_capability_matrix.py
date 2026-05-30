import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestMultiSourceMatrix(unittest.TestCase):
    def test_three_tickers(self):
        from build_phase71_multi_source_capability_matrix import build
        r = build(); cm = r["multi_source_capability_matrix"]
        self.assertEqual(cm["tickers_checked"], 3)
    def test_sources_tracked(self):
        from build_phase71_multi_source_capability_matrix import build
        r = build(); cm = r["multi_source_capability_matrix"]
        self.assertIn("cninfo", cm.get("sources_tracked", []))
    def test_no_mock_fixture(self):
        from build_phase71_multi_source_capability_matrix import build
        r = build(); cm = r["multi_source_capability_matrix"]
        self.assertFalse(cm.get("mock_used",True)); self.assertFalse(cm.get("fixture_used",True))
    def test_pending_zero(self):
        from build_phase71_multi_source_capability_matrix import build
        r = build(); cm = r["multi_source_capability_matrix"]
        self.assertEqual(cm.get("pending_created", -1), 0)
    def test_rows_have_overall(self):
        from build_phase71_multi_source_capability_matrix import build
        r = build(); cm = r["multi_source_capability_matrix"]
        for row in cm["rows"]: self.assertIn("overall", row)
if __name__ == "__main__": unittest.main()
