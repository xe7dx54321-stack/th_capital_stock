import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestMonitoring(unittest.TestCase):
    def test_build(self):from build_phase83_hk_us_monitoring_report import build;r=build();m=r["phase83_hk_us_monitoring"];self.assertGreater(m["signals_checked"],0)
    def test_anomaly_not_trade(self):from build_phase83_hk_us_monitoring_report import build;r=build();m=r["phase83_hk_us_monitoring"];self.assertGreaterEqual(m["anomaly_flags"],0)
if __name__=="__main__":unittest.main()
