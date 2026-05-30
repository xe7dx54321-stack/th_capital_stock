import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestAnomaly(unittest.TestCase):
    def test_build(self):from build_phase82_multi_ticker_anomaly_watch import build;r=build();aw=r["phase82_multi_ticker_anomaly_watch"];self.assertGreater(aw["signals_checked"],0)
    def test_no_trade(self):from build_phase82_multi_ticker_anomaly_watch import build;r=build();aw=r["phase82_multi_ticker_anomaly_watch"];self.assertEqual(aw["business_anomaly"],0)
if __name__=="__main__":unittest.main()
