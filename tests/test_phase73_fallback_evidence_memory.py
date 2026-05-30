import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestEvidenceMemory(unittest.TestCase):
 def test_has_rows(self):
  from run_phase73_write_fallback_evidence_memory import run
  r=run("dry_run");m=r["phase73_fallback_evidence_memory_write"]
  self.assertGreater(len(m.get("rows",[])),0)
 def test_memory_ignored(self):
  from run_phase73_write_fallback_evidence_memory import run
  r=run("dry_run");m=r["phase73_fallback_evidence_memory_write"]
  self.assertTrue(m.get("memory_path_ignored",False))
 def test_no_fake_write(self):
  from run_phase73_write_fallback_evidence_memory import run
  r=run("dry_run");m=r["phase73_fallback_evidence_memory_write"]
  for row in m["rows"]:
   if row.get("reason","").startswith("no_fallback"):
    self.assertEqual(row["records_written"],0)
if __name__=="__main__":unittest.main()
