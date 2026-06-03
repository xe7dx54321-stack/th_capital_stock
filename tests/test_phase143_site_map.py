import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase143_site_map_builder import build_site_map

class TestSiteMap(unittest.TestCase):
    def test_builds(self):
        r = build_site_map()
        self.assertEqual(r['phase143_site_map']['pages'], 10)
        types = set(p['type'] for p in r['phase143_site_map']['site_map'])
        self.assertIn('dashboard', types)
        self.assertIn('detail', types)
        self.assertIn('index', types)

if __name__ == '__main__':
    unittest.main()
