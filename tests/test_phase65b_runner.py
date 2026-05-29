#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/'08_scripts'/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
class T(unittest.TestCase):
 def test_dry_run(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'jobs'))
  from run_phase65b_real_disclosure_evidence_pipeline import run_phase65b
  r=run_phase65b('300308.SZ','dry-run',skip=True)
  p=r['phase65b_real_disclosure_evidence_pipeline']
  self.assertEqual(p['mode'],'dry-run')
  self.assertEqual(len(p['steps']),10)
 def test_skip_network(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'jobs'))
  from run_phase65b_real_disclosure_evidence_pipeline import run_phase65b
  r=run_phase65b('300308.SZ','execute',skip=True)
  p=r['phase65b_real_disclosure_evidence_pipeline']
  self.assertFalse(p['mock_used']);self.assertFalse(p['fixture_used'])
  self.assertEqual(p['pending_created'],0)
 def test_all_steps(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'jobs'))
  from run_phase65b_real_disclosure_evidence_pipeline import run_phase65b
  r=run_phase65b('300308.SZ','dry-run',skip=True)
  names=[s['name'] for s in r['phase65b_real_disclosure_evidence_pipeline']['steps']]
  for n in ['cninfo_source_identity_map','connector_working_parameter_patch','real_metadata_fetch','watchlist_update','brief','dashboard']:
   self.assertIn(n,names)
if __name__=='__main__':unittest.main()
