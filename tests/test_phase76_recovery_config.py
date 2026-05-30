import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase76RecoveryConfig(unittest.TestCase):
    def test_load_config(self):
        from smr_phase76_recovery_config import load_config
        cfg = load_config()
        self.assertEqual(cfg["phase"], "phase76")
        self.assertEqual(cfg["strategy"], "pdf_recovery_and_known_url_breakthrough")
    def test_validate_config(self):
        from smr_phase76_recovery_config import load_config, validate_config
        cfg = load_config(); v = validate_config(cfg)
        self.assertTrue(v["all_pass"])
    def test_save_raw_pdf_false(self):
        from smr_phase76_recovery_config import load_config, validate_config
        cfg = load_config(); v = validate_config(cfg)
        self.assertTrue(v["checks"]["save_raw_pdf"])
    def test_ocr_allowed_false(self):
        from smr_phase76_recovery_config import load_config, validate_config
        cfg = load_config(); v = validate_config(cfg)
        self.assertTrue(v["checks"]["ocr_allowed"])
    def test_mock_allowed_false(self):
        from smr_phase76_recovery_config import load_config, validate_config
        cfg = load_config(); v = validate_config(cfg)
        self.assertTrue(v["checks"]["mock_allowed"])

if __name__ == "__main__": unittest.main()
