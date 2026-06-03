import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase148_activation_plan_builder import build_activation_plans
class T(unittest.TestCase):
 def test_builds(self):
  r=build_activation_plans()
  self.assertEqual(r['phase148_activation_plans']['plans'],5)
  for p in r['phase148_activation_plans']['activation_plans']:
   self.assertTrue(p['requires_owner_approval'])
   self.assertGreaterEqual(len(p['activation_steps']),8)
