import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase142_detail_cannot_conclude_guard import run_detail_cannot_conclude_guard

class TestGuard(unittest.TestCase):
    def test_passes(self):
        r = run_detail_cannot_conclude_guard()
        self.assertEqual(r['phase142_detail_cannot_conclude_guard']['overall_status'], 'pass')
        self.assertEqual(r['phase142_detail_cannot_conclude_guard']['violations'], 0)

if __name__ == '__main__':
    unittest.main()
