import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBoard(unittest.TestCase):
    def test_build(self):from build_phase82_multi_ticker_quant_monitoring_board import build;r=build();b=r["phase82_multi_ticker_quant_monitoring_board"];self.assertGreater(b["tickers_checked"],0)
    def test_covered_blocked(self):from build_phase82_multi_ticker_quant_monitoring_board import build;r=build();b=r["phase82_multi_ticker_quant_monitoring_board"];self.assertGreaterEqual(b["covered_tickers"],0);self.assertGreater(b["blocked_tickers"],0)
    def test_688041_monitoring(self):from build_phase82_multi_ticker_quant_monitoring_board import build;r=build();rows=r["phase82_multi_ticker_quant_monitoring_board"]["rows"];row=[x for x in rows if x["ticker"]=="688041.SH"];self.assertEqual(len(row),1);self.assertIn("monitoring",row[0]["coverage_status"])
    def test_300394_blocked(self):from build_phase82_multi_ticker_quant_monitoring_board import build;r=build();rows=r["phase82_multi_ticker_quant_monitoring_board"]["rows"];row=[x for x in rows if x["ticker"]=="300394.SZ"];self.assertEqual(len(row),1);self.assertIn("blocked",row[0]["coverage_status"])
if __name__=="__main__":unittest.main()
