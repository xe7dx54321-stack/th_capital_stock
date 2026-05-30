import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestEvidenceRerun(unittest.TestCase):
 def test_guard_pass(self):
  from build_phase73_fallback_evidence_rerun import build
  r=build();self.assertEqual(r["phase73_fallback_evidence_rerun"]["guard_status"],"pass")
 def test_management_not_confirmed(self):
  from build_phase73_fallback_evidence_rerun import build
  r=build()
  for row in r["phase73_fallback_evidence_rerun"]["rows"]:
   if row.get("evidence_strength")=="management_commentary":
    self.assertNotEqual(row.get("evidence_strength"),"confirmed")
 def test_no_mock(self):
  from build_phase73_fallback_evidence_rerun import build
  r=build();self.assertFalse(r["phase73_fallback_evidence_rerun"].get("mock_used",True))
 def test_pending_zero(self):
  from build_phase73_fallback_evidence_rerun import build
  r=build();self.assertEqual(r["phase73_fallback_evidence_rerun"].get("pending_created",-1),0)
if __name__=="__main__":unittest.main()
