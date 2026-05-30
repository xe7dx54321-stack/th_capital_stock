import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestEvidenceGain(unittest.TestCase):
 def test_outputs(self):
  from build_phase73_fallback_evidence_gain import build
  r=build();g=r["phase73_fallback_evidence_gain"]
  self.assertIn("phase72",g);self.assertIn("phase73",g)
 def test_gain_zero_ok(self):
  from build_phase73_fallback_evidence_gain import build
  r=build();g=r["phase73_fallback_evidence_gain"]
  self.assertGreaterEqual(g.get("fallback_evidence_gain_delta",-1),0)
 def test_has_blockers(self):
  from build_phase73_fallback_evidence_gain import build
  r=build();g=r["phase73_fallback_evidence_gain"]
  self.assertGreater(len(g.get("source_blockers",[])),0)
 def test_no_mock(self):
  from build_phase73_fallback_evidence_gain import build
  r=build();g=r["phase73_fallback_evidence_gain"]
  self.assertFalse(g.get("mock_used",True));self.assertFalse(g.get("fixture_used",True))
 def test_no_trade(self):
  from build_phase73_fallback_evidence_gain import build
  r=build();g=r["phase73_fallback_evidence_gain"]
  self.assertEqual(g.get("pending_created",-1),0)
if __name__=="__main__":unittest.main()
