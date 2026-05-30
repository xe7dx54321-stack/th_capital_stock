import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestConfig(unittest.TestCase):
    def test_load(self):
        from smr_phase79_real_validation_config import load_config
        c=load_config();self.assertIn("real_network_validation",c.get("strategy",""))
    def test_validate(self):
        from smr_phase79_real_validation_config import validate_config
        v=validate_config();self.assertTrue(v["all_pass"])
    def test_network_enabled(self):
        from smr_phase79_real_validation_config import load_config
        c=load_config();self.assertTrue(c["real_network_validation"]["enabled"])
    def test_raw_disabled(self):
        from smr_phase79_real_validation_config import load_config
        c=load_config();rv=c["real_network_validation"];self.assertFalse(rv["save_raw_pdf"]);self.assertFalse(rv["save_raw_html"])
    def test_ocr_browser_disabled(self):
        from smr_phase79_real_validation_config import load_config
        c=load_config();rv=c["real_network_validation"];self.assertFalse(rv["ocr_allowed"]);self.assertFalse(rv["browser_automation_allowed"])
if __name__=="__main__":unittest.main()
