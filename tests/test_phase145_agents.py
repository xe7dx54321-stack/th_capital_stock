import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase145_agent_registry import build_agent_registry

class TestAgentRegistry(unittest.TestCase):
    def test_builds(self):
        r = build_agent_registry()
        self.assertEqual(r['phase145_agent_registry']['agents'], 8)
        self.assertTrue(r['phase145_agent_registry']['all_research_only'])
        agent_ids = [a['id'] for a in r['phase145_agent_registry']['registry']]
        self.assertIn('opportunity_agent', agent_ids)
        self.assertIn('judge_agent', agent_ids)

if __name__ == '__main__':
    unittest.main()
