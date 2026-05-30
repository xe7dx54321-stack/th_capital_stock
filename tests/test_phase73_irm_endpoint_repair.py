import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestIRMEndpointRepair(unittest.TestCase):
 def test_import(self):
  from smr_phase73_irm_endpoint_repair import repair_irm,test_endpoint_variant
  self.assertTrue(callable(repair_irm))
 def test_sh_unsupported(self):
  from smr_phase73_irm_endpoint_repair import repair_irm
  r=repair_irm("688041.SH");self.assertFalse(r.get("irm_supported",True))
 def test_skip_network(self):
  from smr_phase73_irm_endpoint_repair import repair_irm
  r=repair_irm("300394.SZ",skip_network=True);self.assertEqual(r.get("repair_status"),"skipped")
 def test_no_mock(self):
  from smr_phase73_irm_endpoint_repair import repair_irm
  r=repair_irm("300394.SZ",skip_network=True)
  self.assertFalse(r.get("mock_used",True));self.assertFalse(r.get("fixture_used",True))
 def test_variant_tester(self):
  from smr_phase73_irm_endpoint_repair import test_endpoint_variant
  r=test_endpoint_variant("https://httpbin.org/get","GET")
  self.assertIn("status_code",r)
if __name__=="__main__":unittest.main()
