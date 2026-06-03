import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase147_stage_checker import build_stage_checklist
class T(unittest.TestCase):
 def test_builds(self):
  r=build_stage_checklist()
  self.assertEqual(r['phase147_stage_checklist']['stages'],7)
  self.assertIn('candidate',r['phase147_stage_checklist']['checklist'])
  self.assertIn('display_ready',r['phase147_stage_checklist']['checklist'])
