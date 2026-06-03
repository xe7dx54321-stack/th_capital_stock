import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase151_discovery_sources import build_discovery_sources
class T(unittest.TestCase):
 def test_builds(self):
  r=build_discovery_sources()
  self.assertEqual(r['phase151_discovery_sources']['sources'],9)
  ids=[s['source_id'] for s in r['phase151_discovery_sources']['source_list']]
  self.assertIn('theme_based',ids)
  self.assertIn('supply_chain',ids)
