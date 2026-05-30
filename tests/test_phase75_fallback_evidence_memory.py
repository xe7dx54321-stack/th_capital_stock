import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

class TestPhase75EvidenceMemory(unittest.TestCase):
    def test_dry_run_no_write(self):
        from run_phase75_write_fallback_evidence_memory import run
        r = run("dry_run")
        rep = r["phase75_fallback_evidence_memory_report"]
        self.assertEqual(rep["records_written_total"], 0)
    def test_execute_writes(self):
        from run_phase75_write_fallback_evidence_memory import run
        r = run("execute")
        rep = r["phase75_fallback_evidence_memory_report"]
        self.assertGreater(rep["records_written_total"], 0)
    def test_no_mock(self):
        from run_phase75_write_fallback_evidence_memory import run
        r = run("execute")
        self.assertFalse(r["phase75_fallback_evidence_memory_report"]["mock_used"])

if __name__ == "__main__":
    unittest.main()
