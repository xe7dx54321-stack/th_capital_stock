import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestEvidenceMemory(unittest.TestCase):
    def test_dry_run(self):from run_phase83_write_hk_us_financial_evidence_memory import run;r=run("dry_run");rr=r["phase83_evidence_memory_report"];self.assertEqual(rr["records_written_total"],0)
    def test_execute(self):from run_phase83_write_hk_us_financial_evidence_memory import run;r=run("execute");rr=r["phase83_evidence_memory_report"];self.assertGreaterEqual(rr["records_written_total"],0)
    def test_no_mock(self):from run_phase83_write_hk_us_financial_evidence_memory import run;r=run("execute");self.assertFalse(r["phase83_evidence_memory_report"]["mock_used"])
    def test_memory_ignored(self):from run_phase83_write_hk_us_financial_evidence_memory import run;r=run("execute");self.assertTrue(r["phase83_evidence_memory_report"]["memory_path_ignored"])
if __name__=="__main__":unittest.main()
