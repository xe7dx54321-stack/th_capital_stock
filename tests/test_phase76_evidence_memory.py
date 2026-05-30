import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

class TestEvidenceMemory(unittest.TestCase):
    def test_dry_run_zero(self):
        from run_phase76_write_evidence_memory import run
        r = run("dry_run")
        self.assertEqual(r["phase76_evidence_memory_report"]["records_written_total"], 0)
    def test_no_mock(self):
        from run_phase76_write_evidence_memory import run
        r = run("dry_run")
        self.assertFalse(r["phase76_evidence_memory_report"]["mock_used"])

if __name__ == "__main__": unittest.main()
