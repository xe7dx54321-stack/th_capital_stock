import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestConfig(unittest.TestCase):
    def test_load(self):from smr_phase81_monitoring_config import load_config;c=load_config();self.assertIn("monitoring",c["strategy"])
    def test_target(self):from smr_phase81_monitoring_config import load_config;c=load_config();self.assertEqual(c["target_ticker"],"688041.SH")
    def test_validate(self):from smr_phase81_monitoring_config import validate_config;v=validate_config();self.assertTrue(v["all_pass"])
    def test_signals(self):from smr_phase81_monitoring_config import load_config;c=load_config();s=c["signals"];self.assertIn("revenue",s);self.assertIn("gross_margin",s);self.assertIn("R&D_expense",s)
    def test_thresholds(self):from smr_phase81_monitoring_config import load_config;c=load_config();self.assertGreater(c["signals"]["revenue"]["thresholds"]["strengthened_yoy_pct"],0)
if __name__=="__main__":unittest.main()
