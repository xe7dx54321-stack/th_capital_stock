import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestCapabilityMatrix(unittest.TestCase):
 def test_three_tickers(self):
  from build_phase73_multi_source_capability_matrix import build
  r=build();m=r["phase73_multi_source_capability_matrix"]
  self.assertEqual(m["tickers_checked"],3)
 def test_rows_have_overall(self):
  from build_phase73_multi_source_capability_matrix import build
  r=build();m=r["phase73_multi_source_capability_matrix"]
  for row in m["rows"]:self.assertIn("overall",row)
 def test_no_mock(self):
  from build_phase73_multi_source_capability_matrix import build
  r=build();m=r["phase73_multi_source_capability_matrix"]
  self.assertFalse(m.get("mock_used",True))
 def test_pending_zero(self):
  from build_phase73_multi_source_capability_matrix import build
  r=build();m=r["phase73_multi_source_capability_matrix"]
  self.assertEqual(m.get("pending_created",-1),0)
if __name__=="__main__":unittest.main()
