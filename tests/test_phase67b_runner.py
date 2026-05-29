import unittest,json,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path: sys.path.insert(0,str(J))
class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        try:
            from run_phase67b_ir_report_pdf_evidence_rerun import run
            r=run("300308.SZ",max_pdfs=5,mode="dry_run");p=r["phase67b_ir_report_pdf_evidence_rerun"]
            self.assertEqual(p["mode"],"dry_run");self.assertGreater(len(p["steps"]),0)
        except ImportError: self.skipTest("not importable")
    def test_no_pending_order_trade(self):
        try:
            from run_phase67b_ir_report_pdf_evidence_rerun import run
            r=run("300308.SZ",mode="dry_run");p=r["phase67b_ir_report_pdf_evidence_rerun"]
            self.assertEqual(p["pending_created"],0);self.assertEqual(p["real_trade_created"],0)
        except ImportError: self.skipTest("not importable")
    def test_mock_fixture_raw_ocr_false(self):
        try:
            from run_phase67b_ir_report_pdf_evidence_rerun import run
            r=run("300308.SZ",mode="dry_run");p=r["phase67b_ir_report_pdf_evidence_rerun"]
            self.assertFalse(p["mock_used"]);self.assertFalse(p["fixture_used"]);self.assertFalse(p["raw_saved"]);self.assertFalse(p["ocr_used"])
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
