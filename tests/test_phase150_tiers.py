import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase150_tier_assignment import build_tier_assignments
class T(unittest.TestCase):
 def test_builds(self):
  r=build_tier_assignments()
  tc=r['phase150_tier_assignments']['tier_counts']
  self.assertEqual(tc['core'],3)
  self.assertEqual(tc['watch'],5)
  self.assertEqual(tc['candidate'],5)
  self.assertEqual(r['phase150_tier_assignments']['total'],13)
