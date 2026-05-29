import unittest,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path: sys.path.insert(0,str(R))
class TestDashboard(unittest.TestCase):
    def test_returns_summary(self):
        try:
            from build_phase67b_ir_report_pdf_evidence_dashboard import build
            r=build("300308.SZ");self.assertIn("summary",r)
        except ImportError: self.skipTest("not importable")
    def test_no_pending_order_trade(self):
        try:
            from build_phase67b_ir_report_pdf_evidence_dashboard import build
            r=build("300308.SZ");s=r["summary"]
            self.assertEqual(s["pending_created"],0);self.assertEqual(s["real_trade_created"],0)
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
