import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestPhase75Dashboard(unittest.TestCase):
    def test_build(self):
        from build_phase75_fallback_html_real_execute_dashboard import build
        r = build()
        s = r["summary"]
        self.assertEqual(s["tickers_checked"], 3)
        self.assertTrue(s["network_attempted"])
    def test_pending_zero(self):
        from build_phase75_fallback_html_real_execute_dashboard import build
        r = build()
        self.assertEqual(r["summary"]["pending_created"], 0)
    def test_order_zero(self):
        from build_phase75_fallback_html_real_execute_dashboard import build
        r = build()
        self.assertEqual(r["summary"]["paper_order_created"], 0)
    def test_trade_zero(self):
        from build_phase75_fallback_html_real_execute_dashboard import build
        r = build()
        self.assertEqual(r["summary"]["real_trade_created"], 0)
    def test_no_mock(self):
        from build_phase75_fallback_html_real_execute_dashboard import build
        r = build()
        self.assertFalse(r["summary"]["mock_used"])
    def test_no_raw(self):
        from build_phase75_fallback_html_real_execute_dashboard import build
        r = build()
        self.assertFalse(r["summary"]["raw_saved"])
    def test_fallback_zero(self):
        from build_phase75_fallback_html_real_execute_dashboard import build
        r = build()
        self.assertEqual(r["summary"]["fallback_texts_usable"], 0)
    def test_html_pages_fetched(self):
        from build_phase75_fallback_html_real_execute_dashboard import build
        r = build()
        self.assertEqual(r["summary"]["html_pages_fetched"], 8)

if __name__ == "__main__":
    unittest.main()
