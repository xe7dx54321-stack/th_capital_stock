import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestCompanyIR(unittest.TestCase):
    def test_manual_fill_not_failure(self):
        from build_phase71_company_ir_page_report import build
        r = build(); rep = r.get("company_ir_page_report", r)
        self.assertGreaterEqual(rep.get("manual_fill_required", 0), 1)
    def test_outputs_rows(self):
        from build_phase71_company_ir_page_report import build
        r = build(); rep = r.get("company_ir_page_report", r)
        self.assertGreaterEqual(len(rep.get("rows", [])), 2)
    def test_no_mock_fixture(self):
        from build_phase71_company_ir_page_report import build
        r = build(); rep = r.get("company_ir_page_report", r)
        self.assertFalse(rep.get("mock_used",True))
if __name__ == "__main__": unittest.main()
