#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/'08_scripts'/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
class T(unittest.TestCase):
 def test_brief_has_sections(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'reporting'))
  from build_phase65b_real_disclosure_evidence_brief import build
  r=build('300308.SZ')
  s=r['real_disclosure_evidence_brief']['sections']
  for k in ['observed','implications','can_conclude','cannot_conclude']:
   self.assertIn(k,s)
 def test_no_system_terms(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'reporting'))
  from build_phase65b_real_disclosure_evidence_brief import build
  r=build('300308.SZ')
  s=r['real_disclosure_evidence_brief']['sections']
  all_text=str(s)
  for bad in ['candidate','pending','buy','sell','仓位']:
   self.assertNotIn(bad,all_text.lower())
if __name__=='__main__':unittest.main()
