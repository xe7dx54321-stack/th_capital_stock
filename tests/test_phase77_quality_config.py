import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestQualityConfig(unittest.TestCase):
    def test_load(self):
        from smr_phase77_quality_config import load;cfg=load()
        self.assertEqual(cfg["phase"],"phase77")
    def test_validate(self):
        from smr_phase77_quality_config import validate_config;v=validate_config()
        self.assertTrue(v["all_pass"])
    def test_get_reliability(self):
        from smr_phase77_quality_config import get_reliability
        self.assertGreater(get_reliability("annual_report"),get_reliability("legal_opinion"))
    def test_mock_allowed_false(self):
        from smr_phase77_quality_config import validate_config;v=validate_config()
        self.assertTrue(v["checks"]["mock_allowed"])
if __name__=="__main__":unittest.main()
