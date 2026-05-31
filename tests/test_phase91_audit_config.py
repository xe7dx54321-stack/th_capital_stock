import unittest, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase91_audit_config import load_config, get_universe, get_dimensions, get_taxonomy, get_known_blocked, get_known_gaps

class TestConfig(unittest.TestCase):
    def test_load(self):
        cfg=load_config()
        self.assertEqual(cfg["phase"],"phase91")
    def test_universe_8(self):
        self.assertEqual(len(get_universe()),8)
    def test_dimensions_15(self):
        self.assertEqual(len(get_dimensions()),15)
    def test_taxonomy_10(self):
        self.assertEqual(len(get_taxonomy()),10)
    def test_blocked_has_300394(self):
        self.assertIn("300394.SZ",get_known_blocked())
    def test_gaps_have_688041(self):
        self.assertIn("688041.SH",get_known_gaps())
    def test_safety_no_mock(self):
        cfg=load_config()
        self.assertFalse(cfg["safety"]["mock_allowed"])
    def test_no_research_framework(self):
        cfg=load_config()
        self.assertFalse(cfg["safety"]["research_framework_creation_allowed"])
    def test_no_trade(self):
        cfg=load_config()
        self.assertFalse(cfg["safety"]["real_trade_allowed"])
        self.assertFalse(cfg["safety"]["paper_order_allowed"])
        self.assertFalse(cfg["safety"]["pending_allowed"])
    def test_no_target_price(self):
        cfg=load_config()
        self.assertFalse(cfg["safety"]["target_price_output_allowed"])
