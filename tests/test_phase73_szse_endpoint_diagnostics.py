import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestSZSEDiagnostics(unittest.TestCase):
 def test_import(self):
  from smr_phase73_szse_endpoint_diagnostics import diagnose_szse,test_szse_variant
  self.assertTrue(callable(diagnose_szse))
 def test_sh_unsupported(self):
  from smr_phase73_szse_endpoint_diagnostics import diagnose_szse
  r=diagnose_szse("688041.SH");self.assertEqual(r.get("diagnostic_status"),"not_applicable_sh")
 def test_skip_network(self):
  from smr_phase73_szse_endpoint_diagnostics import diagnose_szse
  r=diagnose_szse("300394.SZ",skip_network=True);self.assertEqual(r.get("diagnostic_status"),"skipped")
 def test_no_mock(self):
  from smr_phase73_szse_endpoint_diagnostics import diagnose_szse
  r=diagnose_szse("300394.SZ",skip_network=True)
  self.assertFalse(r.get("mock_used",True));self.assertFalse(r.get("fixture_used",True))
if __name__=="__main__":unittest.main()
