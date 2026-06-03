import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'jobs'))
from run_phase148_candidate_pipeline import run
class T(unittest.TestCase):
 def test_dry(self):
  r=run('dry-run')
  p=r['phase148_candidate_pipeline']
  self.assertEqual(p['candidates'],5)
  self.assertFalse(p['auto_add_to_watchlist'])
  self.assertEqual(p['quality_gate'],'pass')
