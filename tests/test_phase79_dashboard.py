import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestDashboard(unittest.TestCase):
    def test_build(self):
        from build_phase79_high_value_report_quant_dashboard import build
        r=build();s=r["summary"]
        self.assertEqual(s["tickers_checked"],3)
        self.assertEqual(s["pending_created"],0)
        self.assertFalse(s["mock_used"])
        self.assertFalse(s["ocr_used"])
    def test_metrics(self):
        from build_phase79_high_value_report_quant_dashboard import build
        r=build();s=r["summary"]
        self.assertGreater(s["metrics_extracted"],0)
        self.assertTrue(s["real_network_validation_attempted"])
if __name__=="__main__":unittest.main()
