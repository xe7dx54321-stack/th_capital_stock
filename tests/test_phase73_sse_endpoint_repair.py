import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestSSEEndpointRepair(unittest.TestCase):
 def test_import(self):
  from smr_phase73_sse_endpoint_repair import repair_sse,test_sse_variant
  self.assertTrue(callable(repair_sse))
 def test_sz_unsupported(self):
  from smr_phase73_sse_endpoint_repair import repair_sse
  r=repair_sse("300394.SZ");self.assertEqual(r.get("repair_status"),"not_applicable_sz")
 def test_skip_network(self):
  from smr_phase73_sse_endpoint_repair import repair_sse
  r=repair_sse("688041.SH",skip_network=True);self.assertEqual(r.get("repair_status"),"skipped")
 def test_no_mock(self):
  from smr_phase73_sse_endpoint_repair import repair_sse
  r=repair_sse("688041.SH",skip_network=True)
  self.assertFalse(r.get("mock_used",True));self.assertFalse(r.get("fixture_used",True))
if __name__=="__main__":unittest.main()
