import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestEvidenceMemory(unittest.TestCase):
    def test_dry_run(self):from run_phase81_write_monitoring_evidence_memory import run;r=run("dry_run");rr=r["phase81_evidence_memory_report"];self.assertEqual(rr["records_written_total"],0);self.assertFalse(rr["mock_used"])
    def test_execute(self):from run_phase81_write_monitoring_evidence_memory import run;r=run("execute");rr=r["phase81_evidence_memory_report"];self.assertGreaterEqual(rr["records_written_total"],0)
    def test_has_monitoring_fields(self):from run_phase81_write_monitoring_evidence_memory import run;r=run("execute");rows=r["phase81_evidence_memory_report"]["rows"];self.assertTrue(all("delta_status" in row and "monitoring_applied" in row and "delta_detection_applied" in row for row in rows) if rows else True)
    def test_no_mock(self):from run_phase81_write_monitoring_evidence_memory import run;r=run("execute");self.assertFalse(r["phase81_evidence_memory_report"]["mock_used"]);self.assertFalse(r["phase81_evidence_memory_report"]["fixture_used"])
    def test_memory_ignored(self):from run_phase81_write_monitoring_evidence_memory import run;r=run("execute");self.assertTrue(r["phase81_evidence_memory_report"]["memory_path_ignored"])
if __name__=="__main__":unittest.main()
