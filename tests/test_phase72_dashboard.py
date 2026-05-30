import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestDashboard(unittest.TestCase):
    def test_outputs(self):
        from build_phase72_fallback_real_text_dashboard import build
        r = build(); s = r["summary"]
        self.assertEqual(s.get("tickers_checked", 0), 3)
    def test_pending_zero(self):
        from build_phase72_fallback_real_text_dashboard import build
        r = build(); s = r["summary"]
        self.assertEqual(s.get("pending_created", -1), 0)
    def test_no_mock(self):
        from build_phase72_fallback_real_text_dashboard import build
        r = build(); s = r["summary"]
        self.assertFalse(s.get("mock_used",True))
    def test_brief_quality(self):
        from build_phase72_fallback_real_text_dashboard import build
        r = build(); s = r["summary"]
        self.assertEqual(s.get("brief_quality_status", ""), "pass")
if __name__ == "__main__": unittest.main()
