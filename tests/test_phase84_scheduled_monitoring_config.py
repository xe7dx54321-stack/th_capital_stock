import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestConfig(unittest.TestCase):
    def test_build(self):from build_phase84_scheduled_monitoring_config_report import build;r=build();v=r["phase84_scheduled_monitoring_config"]["validation"];self.assertTrue(v["all_pass"])
    def test_universe_8(self):from build_phase84_scheduled_monitoring_config_report import build;r=build();c=r["phase84_scheduled_monitoring_config"]["config"];self.assertEqual(len(c["universe"]["tickers"]),8)
    def test_cron_disabled(self):from build_phase84_scheduled_monitoring_config_report import build;r=build();c=r["phase84_scheduled_monitoring_config"]["config"];self.assertFalse(c["schedule"]["cron_enabled"])
    def test_valuation_disabled(self):from build_phase84_scheduled_monitoring_config_report import build;r=build();c=r["phase84_scheduled_monitoring_config"]["config"];self.assertFalse(c["safety"]["valuation_enabled"])
    def test_portfolio_disabled(self):from build_phase84_scheduled_monitoring_config_report import build;r=build();c=r["phase84_scheduled_monitoring_config"]["config"];self.assertFalse(c["safety"]["portfolio_construction_enabled"])
    def test_no_mock(self):from build_phase84_scheduled_monitoring_config_report import build;r=build();c=r["phase84_scheduled_monitoring_config"]["config"];self.assertFalse(c["safety"]["mock_allowed"])
if __name__=="__main__":unittest.main()
