import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestEvidenceMemory(unittest.TestCase):
    def test_dry_run_zero(self):
        from run_phase77_write_evidence_memory import run
        r=run("dry_run")
        self.assertEqual(r["phase77_evidence_memory_report"]["records_written_total"],0)
    def test_execute_writes(self):
        from run_phase77_write_evidence_memory import run
        r=run("execute")
        self.assertGreater(r["phase77_evidence_memory_report"]["records_written_total"],0)
    def test_has_reliability_score(self):
        from run_phase77_write_evidence_memory import run
        r=run("execute")
        for row in r["phase77_evidence_memory_report"]["rows"]:
            self.assertIn("reliability_score",row)
if __name__=="__main__":unittest.main()
