import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_local_open_instruction_builder import build_local_open_instruction

class TestLocalOpen(unittest.TestCase):
    def test_builds(self):
        r = build_local_open_instruction()
        self.assertTrue(r['phase141_local_open_instruction_builder']['static_html_only'])
        self.assertFalse(r['phase141_local_open_instruction_builder']['external_js_allowed'])
        self.assertFalse(r['phase141_local_open_instruction_builder']['external_cdn_allowed'])
        self.assertFalse(r['phase141_local_open_instruction_builder']['local_server_enabled'])

if __name__ == '__main__':
    unittest.main()
