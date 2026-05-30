import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestAnomalyWatch(unittest.TestCase):
    def test_build(self):from build_phase81_anomaly_watch_report import build;r=build();aw=r["phase81_anomaly_watch"];self.assertGreater(aw["signals_checked"],0)
    def test_anomaly_count(self):from build_phase81_anomaly_watch_report import build;r=build();aw=r["phase81_anomaly_watch"];self.assertGreaterEqual(aw["anomaly_flags"],0)
if __name__=="__main__":unittest.main()
