import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestEvidenceMemory(unittest.TestCase):
    def test_dry_run_zero(self):
        from run_phase79_write_evidence_memory import run
        r=run("dry_run");m=r["phase79_evidence_memory_report"]
        self.assertEqual(m["records_written_total"],0)
    def test_execute_writes(self):
        from run_phase79_write_evidence_memory import run
        r=run("execute");m=r["phase79_evidence_memory_report"]
        self.assertGreater(m["records_written_total"],0)
    def test_has_metric_fields(self):
        from run_phase79_write_evidence_memory import run
        r=run("execute");rows=r["phase79_evidence_memory_report"]["rows"]
        for row in rows:
            self.assertIn("metric_period",row)
            self.assertIn("unit",row)
            self.assertIn("source_section",row)
if __name__=="__main__":unittest.main()
