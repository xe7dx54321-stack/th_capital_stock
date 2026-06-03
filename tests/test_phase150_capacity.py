import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase150_capacity_model import build_capacity_model
class T(unittest.TestCase):
 def test_builds(self):
  r=build_capacity_model()
  m=r['phase150_capacity_model']['model']
  self.assertEqual(m['max_total'],50)
  self.assertIn('promotion_rules',m)
  self.assertIn('demotion_rules',m)
  self.assertGreater(len(m['promotion_rules']),0)
