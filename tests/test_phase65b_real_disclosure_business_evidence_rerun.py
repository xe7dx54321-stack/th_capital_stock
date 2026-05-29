#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/'08_scripts'/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
class T(unittest.TestCase):
 def test_skip_delta_zero(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'reporting'))
  from build_phase65b_real_disclosure_business_evidence_rerun import build
  r=build('300308.SZ',skip=True)
  b=r['real_disclosure_business_evidence_rerun']
  self.assertFalse(b['real_disclosure_text_used'])
  self.assertEqual(b['evidence_gain_delta'],0)
 def test_no_mock_fixture(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'reporting'))
  from build_phase65b_real_disclosure_business_evidence_rerun import build
  r=build('300308.SZ',skip=True)
  b=r['real_disclosure_business_evidence_rerun']
  self.assertFalse(b['mock_used']);self.assertFalse(b['fixture_used'])
if __name__=='__main__':unittest.main()
