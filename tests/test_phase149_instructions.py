import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase149_agent_instructions import build_agent_instructions
class T(unittest.TestCase):
 def test_builds(self):
  r=build_agent_instructions()
  self.assertEqual(r['phase149_agent_instructions']['agents'],8)
  for inst in r['phase149_agent_instructions']['instructions']:
   self.assertIn('role',inst)
   self.assertIn('banned_actions',inst)
   self.assertIn('cannot_conclude',inst)
   self.assertIn('judge_trigger',inst)
   self.assertIn('handoff_to',inst)
  agent_ids=[i['agent_id'] for i in r['phase149_agent_instructions']['instructions']]
  self.assertIn('judge_agent',agent_ids)
  self.assertIn('brief_agent',agent_ids)
