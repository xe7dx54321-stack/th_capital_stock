import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase146_agent_memory import build_agent_memory
class T(unittest.TestCase):
 def test_builds(self):
  r=build_agent_memory()
  self.assertEqual(r['phase146_agent_memory']['agents'],8)
  self.assertTrue(r['phase146_agent_memory']['all_research_only'])
