import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'jobs'))
from run_phase150_tiering_pipeline import run
class T(unittest.TestCase):
 def test_dry(self):
  r=run('dry-run')
  p=r['phase150_tiering_pipeline']
  self.assertEqual(p['tiers']['core'],3)
  self.assertEqual(p['total_tracked'],13)
  self.assertEqual(p['quality_gate'],'pass')
  self.assertFalse(p['mock_used'])
