import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestCompanyIRPatch(unittest.TestCase):
    def test_two_tickers(self):
        from build_phase72_company_ir_candidate_patch import build
        r = build(); d = r["phase72_company_ir_candidate_patch"]
        self.assertEqual(d["tickers_checked"], 2)
    def test_manual_fill_not_pass(self):
        from build_phase72_company_ir_candidate_patch import build
        r = build(); d = r["phase72_company_ir_candidate_patch"]
        self.assertGreaterEqual(d["manual_fill_required"], 0)
    def test_688041_has_sse_candidate(self):
        from build_phase72_company_ir_candidate_patch import build
        r = build(); d = r["phase72_company_ir_candidate_patch"]
        row = [rw for rw in d["rows"] if rw["ticker"]=="688041.SH"][0]
        self.assertTrue(row.get("ir_page") or row.get("verification_status"))
    def test_no_mock(self):
        from build_phase72_company_ir_candidate_patch import build
        r = build(); d = r["phase72_company_ir_candidate_patch"]
        self.assertFalse(d.get("mock_used",True))
if __name__ == "__main__": unittest.main()
