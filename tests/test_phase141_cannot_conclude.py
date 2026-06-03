import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_cannot_conclude_guard import run_cannot_conclude_guard

class TestCannotConclude(unittest.TestCase):
    def test_guard_passes(self):
        r = run_cannot_conclude_guard()
        self.assertEqual(r['phase141_cannot_conclude_guard']['overall_status'], 'pass')
        self.assertEqual(r['phase141_cannot_conclude_guard']['violations'], 0)
        self.assertFalse(r['phase141_cannot_conclude_guard']['mock_used'])

if __name__ == '__main__':
    unittest.main()
