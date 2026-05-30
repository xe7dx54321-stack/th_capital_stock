import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        from run_phase77_pdf_evidence_quality_pipeline import run
        r=run("dry_run");rr=r["phase77_pdf_evidence_quality_pipeline"]
        self.assertEqual(rr["mode"],"dry_run")
    def test_execute(self):
        from run_phase77_pdf_evidence_quality_pipeline import run
        r=run("execute");rr=r["phase77_pdf_evidence_quality_pipeline"]
        self.assertEqual(rr["pending_created"],0)
        self.assertEqual(rr["paper_order_created"],0)
        self.assertEqual(rr["real_trade_created"],0)
    def test_no_mock(self):
        from run_phase77_pdf_evidence_quality_pipeline import run
        r=run("execute");self.assertFalse(r["phase77_pdf_evidence_quality_pipeline"]["mock_used"])
if __name__=="__main__":unittest.main()
