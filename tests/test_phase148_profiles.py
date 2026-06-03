import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase148_candidate_profiles import build_candidate_profiles
class T(unittest.TestCase):
 def test_builds(self):
  r=build_candidate_profiles()
  self.assertEqual(r['phase148_candidate_profiles']['candidates'],5)
  self.assertFalse(r['phase148_candidate_profiles']['auto_add_to_watchlist'])
  tickers=[p['ticker'] for p in r['phase148_candidate_profiles']['profiles']]
  for t in ['TSM','ASML','SNOW','MU','AMD']:
   self.assertIn(t,tickers)
