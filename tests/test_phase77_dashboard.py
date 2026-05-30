import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestDashboard(unittest.TestCase):
    def test_build(self):
        from build_phase77_pdf_evidence_quality_dashboard import build
        r=build();s=r["summary"]
        self.assertEqual(s["tickers_checked"],3)
        self.assertEqual(s["pending_created"],0)
        self.assertEqual(s["paper_order_created"],0)
        self.assertEqual(s["real_trade_created"],0)
if __name__=="__main__":unittest.main()
