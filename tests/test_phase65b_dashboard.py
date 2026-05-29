#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/'08_scripts'/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
class T(unittest.TestCase):
 def test_dashboard_no_mock(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'reporting'))
  from build_phase65b_real_disclosure_evidence_dashboard import build
  r=build(skip=True)
  s=r['summary']
  self.assertFalse(s['mock_used']);self.assertFalse(s['fixture_used'])
  self.assertFalse(s['raw_saved']);self.assertFalse(s['ocr_used'])
 def test_pending_zero(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'reporting'))
  from build_phase65b_real_disclosure_evidence_dashboard import build
  r=build(skip=True)
  s=r['summary']
  self.assertEqual(s['pending_created'],0);self.assertEqual(s['paper_order_created'],0)
 def test_stock_param(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'reporting'))
  from build_phase65b_real_disclosure_evidence_dashboard import build
  r=build(skip=True)
  self.assertEqual(r['summary']['stock_param'],'300308,9900022016')
if __name__=='__main__':unittest.main()
