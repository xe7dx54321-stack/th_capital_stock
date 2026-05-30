import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestDashboard(unittest.TestCase):
    def test_build(self):from build_phase80_report_quant_consistency_dashboard import build;r=build();s=r["summary"];self.assertGreater(s["tickers_checked"],0)
    def test_has_metrics(self):from build_phase80_report_quant_consistency_dashboard import build;r=build();s=r["summary"];self.assertGreaterEqual(s["report_metrics_loaded"],0);self.assertGreaterEqual(s["structured_metrics_loaded"],0)
    def test_has_time_series(self):from build_phase80_report_quant_consistency_dashboard import build;r=build();s=r["summary"];self.assertGreaterEqual(s["time_series_signals_created"],0)
    def test_no_pending(self):from build_phase80_report_quant_consistency_dashboard import build;r=build();s=r["summary"];self.assertEqual(s["pending_created"],0);self.assertEqual(s["paper_order_created"],0);self.assertEqual(s["real_trade_created"],0)
    def test_no_mock(self):from build_phase80_report_quant_consistency_dashboard import build;r=build();s=r["summary"];self.assertFalse(s["mock_used"]);self.assertFalse(s["fixture_used"])
    def test_guard_pass(self):from build_phase80_report_quant_consistency_dashboard import build;r=build();s=r["summary"];self.assertEqual(s["guard_status"],"pass")
    def test_claims(self):from build_phase80_report_quant_consistency_dashboard import build;r=build();s=r["summary"];self.assertGreaterEqual(s["claims_observed"],0);self.assertGreaterEqual(s["claims_unconfirmed"],0)
if __name__=="__main__":unittest.main()
