import unittest, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase92_config import load_config, get_universe, get_signal_types, get_keywords, get_ticker_entities

class TestConfig(unittest.TestCase):
    def test_load(self):
        cfg=load_config()
        self.assertEqual(cfg["phase"],"phase92")
    def test_universe(self):
        self.assertEqual(len(get_universe()),8)
    def test_signals(self):
        self.assertEqual(len(get_signal_types()),10)
    def test_keywords(self):
        self.assertGreater(len(get_keywords("cn")),10)
    def test_entities(self):
        self.assertIn("NVDA",get_ticker_entities())
    def test_no_mock(self):
        self.assertFalse(load_config()["safety"]["mock_allowed"])
    def test_no_trade(self):
        c=load_config()["safety"]
        self.assertFalse(c["real_trade_allowed"])
        self.assertFalse(c["pending_allowed"])
    def test_no_target_price(self):
        self.assertFalse(load_config()["safety"]["target_price_output_allowed"])
    def test_no_position_sizing(self):
        self.assertFalse(load_config()["safety"]["position_sizing_allowed"])
