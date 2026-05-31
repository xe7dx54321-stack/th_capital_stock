import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestConfig(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_config_report import build;r=build();v=r["phase85_valuation_config"]["validation"];self.assertTrue(v["all_pass"])
    def test_8_tickers(self):from build_phase85_valuation_config_report import build;r=build();c=r["phase85_valuation_config"]["config"];self.assertEqual(len(c["target_tickers"]),8)
    def test_300394_blocked(self):from build_phase85_valuation_config_report import build;r=build();c=r["phase85_valuation_config"]["config"];self.assertIn("300394.SZ",c["known_blocked"])
    def test_5_bands(self):from build_phase85_valuation_config_report import build;r=build();c=r["phase85_valuation_config"]["config"];self.assertEqual(len(c["bands"]),5)
    def test_no_mock(self):from build_phase85_valuation_config_report import build;r=build();c=r["phase85_valuation_config"]["config"];self.assertFalse(c["safety"]["mock_allowed"])
if __name__=="__main__":unittest.main()
