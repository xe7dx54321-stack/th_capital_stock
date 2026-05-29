#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class T(unittest.TestCase):
 def test_skip_network(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
  from build_phase65b_cninfo_connector_working_parameter_patch import build
  r=build("300308.SZ",skip=True)
  p=r["cninfo_connector_working_parameter_patch"]
  self.assertTrue(p["identity_map_used"])
  self.assertEqual(p["status"],"skipped_network_disabled")
 def test_no_identity_for_unknown(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
  from build_phase65b_cninfo_connector_working_parameter_patch import build
  r=build("999999.SZ",skip=True)
  self.assertFalse(r["cninfo_connector_working_parameter_patch"]["identity_map_used"])
 def test_no_mock_fixture(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
  from build_phase65b_cninfo_connector_working_parameter_patch import build
  r=build("300308.SZ",skip=True)
  p=r["cninfo_connector_working_parameter_patch"]
  self.assertFalse(p["mock_used"]);self.assertFalse(p["fixture_used"])
if __name__=="__main__":unittest.main()
