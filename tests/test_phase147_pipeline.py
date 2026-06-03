import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase147_onboarding_pipeline import build_onboarding_pipeline
class T(unittest.TestCase):
 def test_builds(self):
  r=build_onboarding_pipeline()
  s=r['phase147_onboarding_pipeline']['summary']
  self.assertEqual(s['onboarded'],8)
  self.assertEqual(s['candidates'],5)
  self.assertTrue(r['phase147_onboarding_pipeline']['research_only'])
