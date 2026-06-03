import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'jobs'))
from run_phase147_onboarding_pipeline import run
class T(unittest.TestCase):
 def test_dry(self):
  r=run('dry-run')
  p=r['phase147_onboarding_pipeline']
  self.assertEqual(p['onboarded'],8)
  self.assertEqual(p['quality_gate'],'pass')
  self.assertFalse(p['mock_used'])
