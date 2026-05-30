import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestCompanyIRFetch(unittest.TestCase):
    def test_manual_not_failure(self):
        from build_phase72_company_ir_real_fetch_report import build
        r = build(); d = r["phase72_company_ir_real_fetch"]
        self.assertGreaterEqual(d["manual_fill_required"], 0)
    def test_no_mock(self):
        from build_phase72_company_ir_real_fetch_report import build
        r = build(); d = r["phase72_company_ir_real_fetch"]
        self.assertFalse(d.get("mock_used",True))
    def test_no_raw(self):
        from build_phase72_company_ir_real_fetch_report import build
        r = build(); d = r["phase72_company_ir_real_fetch"]
        self.assertFalse(d.get("raw_saved", True))
if __name__ == "__main__": unittest.main()
