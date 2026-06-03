import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'jobs'))
from run_phase151_discovery_pipeline import run
class T(unittest.TestCase):
 def test_dry(self):
  r=run('dry-run')
  p=r['phase151_discovery_pipeline']
  self.assertEqual(p['discovery_sources'],9)
  self.assertEqual(p['candidates_discovered'],8)
  self.assertEqual(p['quality_gate'],'pass')
