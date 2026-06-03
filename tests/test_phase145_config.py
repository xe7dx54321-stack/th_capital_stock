import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase145_config import load_phase145_config

class TestPhase145Config(unittest.TestCase):
    def test_loads(self):
        cfg = load_phase145_config()
        self.assertTrue(cfg['research_only'])
        self.assertEqual(cfg['agent_count'], 8)
        self.assertFalse(cfg['auto_dispatch_allowed'])

if __name__ == '__main__':
    unittest.main()
