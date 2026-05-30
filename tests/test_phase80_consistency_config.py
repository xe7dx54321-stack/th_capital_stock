import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestConfig(unittest.TestCase):
    def test_load(self):from smr_phase80_consistency_config import load_config;c=load_config();self.assertIn("consistency",c["strategy"])
    def test_target(self):from smr_phase80_consistency_config import load_config;c=load_config();self.assertEqual(c["target_ticker"],"688041.SH")
    def test_validate(self):from smr_phase80_consistency_config import validate_config;v=validate_config();self.assertTrue(v["all_pass"])
    def test_metrics_covered(self):from smr_phase80_consistency_config import load_config;c=load_config();m=c["metrics"];self.assertIn("revenue",m);self.assertIn("gross_margin",m);self.assertIn("R&D_expense",m)
    def test_tolerance(self):from smr_phase80_consistency_config import load_config;c=load_config();self.assertGreater(c["metrics"]["revenue"]["tolerance_pct"],0);self.assertGreater(c["metrics"]["gross_margin"]["tolerance_pct"],0)
if __name__=="__main__":unittest.main()
