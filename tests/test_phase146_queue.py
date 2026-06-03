import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase146_task_queue import build_task_queue
class T(unittest.TestCase):
 def test_builds(self):
  r=build_task_queue()
  self.assertEqual(r['phase146_task_queue']['summary']['total'],4)
  self.assertGreater(r['phase146_task_queue']['summary']['blocked'],0)
