import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase75RealExecuteConfig(unittest.TestCase):
    def test_load_config(self):
        from smr_phase75_real_execute_config import load_config
        cfg = load_config()
        self.assertEqual(cfg["phase"], "phase75")
        self.assertTrue(cfg["real_execute_required"])
    def test_validate_config(self):
        from smr_phase75_real_execute_config import load_config, validate_config
        cfg = load_config()
        v = validate_config(cfg)
        self.assertTrue(v["all_pass"])
    def test_save_raw_html_false(self):
        from smr_phase75_real_execute_config import load_config, validate_config
        cfg = load_config()
        v = validate_config(cfg)
        self.assertTrue(v["checks"]["save_raw_html"])
    def test_mock_allowed_false(self):
        from smr_phase75_real_execute_config import load_config, validate_config
        cfg = load_config()
        v = validate_config(cfg)
        self.assertTrue(v["checks"]["mock_allowed"])
    def test_fixture_allowed_false(self):
        from smr_phase75_real_execute_config import load_config, validate_config
        cfg = load_config()
        v = validate_config(cfg)
        self.assertTrue(v["checks"]["fixture_allowed"])
    def test_real_execute_required_true(self):
        from smr_phase75_real_execute_config import load_config
        cfg = load_config()
        self.assertTrue(cfg["real_execute_required"])

if __name__ == "__main__":
    unittest.main()
