import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'jobs'))
from run_phase146_agent_memory_pipeline import run_pipeline
class T(unittest.TestCase):
 def test_dry(self):
  r=run_pipeline('dry-run')
  p=r['phase146_agent_memory_pipeline']
  self.assertEqual(p['agents_with_memory'],8)
  self.assertEqual(p['quality_gate'],'pass')
  self.assertFalse(p['mock_used'])
 def test_safety(self):
  for m in ['dry-run','execute','skip-network']:
   r=run_pipeline(m); p=r['phase146_agent_memory_pipeline']
   self.assertFalse(p['mock_used'])
   self.assertEqual(p['paper_order_created'],0)
