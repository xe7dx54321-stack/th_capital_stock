import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestDashboard(unittest.TestCase):
    def test_build(self):
        from build_phase78_chinese_keyword_high_value_report_dashboard import build
        r=build();s=r["summary"]
        self.assertEqual(s["tickers_checked"],3)
        self.assertEqual(s["pending_created"],0)
        self.assertEqual(s["paper_order_created"],0)
        self.assertEqual(s["real_trade_created"],0)
        self.assertFalse(s["mock_used"])
        self.assertFalse(s["ocr_used"])
    def test_evidence_counts(self):
        from build_phase78_chinese_keyword_high_value_report_dashboard import build
        r=build();s=r["summary"]
        self.assertGreater(s["deep_evidence_created"],0)
        self.assertGreater(s["high_value_texts_usable"],0)
if __name__=="__main__":unittest.main()
