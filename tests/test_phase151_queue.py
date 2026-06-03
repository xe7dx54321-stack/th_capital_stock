import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase151_discovery_queue import build_discovery_queue
class T(unittest.TestCase):
 def test_builds(self):
  r=build_discovery_queue()
  self.assertEqual(r['phase151_discovery_queue']['candidates_discovered'],8)
  self.assertFalse(r['phase151_discovery_queue']['auto_add_to_watchlist'])
  s=r['phase151_discovery_queue']['summary']
  self.assertGreater(s['by_priority']['high'],0)
