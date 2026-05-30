import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestCapabilityMatrix(unittest.TestCase):
    def test_build(self):from build_phase84_multi_source_capability_matrix import build;r=build();m=r["phase84_multi_source_capability_matrix"];self.assertGreater(m["tickers_checked"],0)
    def test_daily_monitoring(self):from build_phase84_multi_source_capability_matrix import build;r=build();m=r["phase84_multi_source_capability_matrix"];self.assertEqual(m["daily_monitoring_enabled"],7)
    def test_blocked(self):from build_phase84_multi_source_capability_matrix import build;r=build();m=r["phase84_multi_source_capability_matrix"];self.assertEqual(m["blocked"],1)
    def test_no_pending(self):from build_phase84_multi_source_capability_matrix import build;r=build();m=r["phase84_multi_source_capability_matrix"];self.assertEqual(m["pending_created"],0)
if __name__=="__main__":unittest.main()
