import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase144_config import load_phase144_config

class TestPhase144Config(unittest.TestCase):
    def test_loads(self):
        cfg = load_phase144_config()
        self.assertTrue(cfg['research_only'])
        self.assertTrue(cfg['feedback_form_enabled'])
        self.assertTrue(cfg['manual_confirmation_enabled'])
        self.assertFalse(cfg['external_js_allowed'])

if __name__ == '__main__':
    unittest.main()
