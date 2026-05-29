#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_real_network_validation_config import get_network_validation, build_validation_config_report

class TestConfig(unittest.TestCase):
    def test_save_raw_false(self):
        cfg = get_network_validation()
        self.assertFalse(cfg['save_raw_content'])
    def test_ocr_false(self):
        cfg = get_network_validation()
        self.assertFalse(cfg['ocr_allowed'])
    def test_mock_fallback_false(self):
        cfg = get_network_validation()
        self.assertFalse(cfg['allow_mock_fallback'])
    def test_fixture_fallback_false(self):
        cfg = get_network_validation()
        self.assertFalse(cfg['allow_fixture_fallback'])
    def test_report_builds(self):
        r = build_validation_config_report()
        self.assertEqual(r['network_validation']['save_raw'], False)
if __name__=='__main__': unittest.main()
