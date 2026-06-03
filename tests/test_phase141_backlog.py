import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase141_backlog_update import build_backlog_update

class TestBacklog(unittest.TestCase):
    def test_builds(self):
        r = build_backlog_update()
        self.assertIn('phase141_backlog_update', r)
        self.assertGreater(r['phase141_backlog_update']['items'], 0)
        self.assertTrue(r['phase141_backlog_update']['not_trade'])
        backlog = r['phase141_backlog_update']['backlog']
        blockers = [b for b in backlog if b['status'] == 'blocked']
        self.assertGreater(len(blockers), 0)

if __name__ == '__main__':
    unittest.main()
