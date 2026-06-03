import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase145_orchestrator import build_orchestrator_state

class TestOrchestrator(unittest.TestCase):
    def test_builds(self):
        r = build_orchestrator_state()
        s = r['phase145_orchestrator']['summary']
        self.assertEqual(s['total_tasks'], 8)
        self.assertGreater(s['completed'], 0)
        self.assertEqual(s['trade_actions'], 0)
        self.assertTrue(s['all_research_only'])

if __name__ == '__main__':
    unittest.main()
