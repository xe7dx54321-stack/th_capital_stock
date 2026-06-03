import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_navigation_anchor_system import build_navigation_anchor_system

class TestNavigation(unittest.TestCase):
    def test_nav_builds(self):
        r = build_navigation_anchor_system()
        self.assertIn('phase141_navigation_anchor_system', r)
        self.assertTrue(r['phase141_navigation_anchor_system']['ready'])
        nav = r['phase141_navigation_anchor_system']['nav']
        self.assertIn('Ticker Cards', nav)
        self.assertIn('Thesis Library', nav)
        self.assertIn('Evidence', nav)
        self.assertIn('Delivery', nav)

if __name__ == '__main__':
    unittest.main()
