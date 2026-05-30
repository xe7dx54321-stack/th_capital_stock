import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestEvidenceGain(unittest.TestCase):
 def test_outputs(self):
  from build_phase74_fallback_evidence_gain import build
  r=build();g=r["phase74_fallback_evidence_gain"]
  self.assertIn("phase73",g);self.assertIn("phase74",g)
 def test_gain_zero_ok(self):
  from build_phase74_fallback_evidence_gain import build
  r=build();g=r["phase74_fallback_evidence_gain"]
  self.assertGreaterEqual(g.get("fallback_evidence_gain_delta",-1),0)
 def test_has_blockers(self):
  from build_phase74_fallback_evidence_gain import build
  r=build();g=r["phase74_fallback_evidence_gain"]
  self.assertGreater(len(g.get("source_blockers",[])),0)
 def test_no_mock(self):
  from build_phase74_fallback_evidence_gain import build
  r=build();self.assertFalse(r["phase74_fallback_evidence_gain"].get("mock_used",True))
if __name__=="__main__":unittest.main()
