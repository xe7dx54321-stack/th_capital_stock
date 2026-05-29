#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/'08_scripts'/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
class T(unittest.TestCase):
 def test_zero_delta(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'reporting'))
  from build_phase65b_watchlist_update_from_real_disclosure import build
  r=build('300308.SZ',evidence_delta=0)
  w=r['watchlist_update_from_real_disclosure']
  self.assertEqual(w['claims_strengthened'],[])
 def test_positive_delta(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'reporting'))
  from build_phase65b_watchlist_update_from_real_disclosure import build
  r=build('300308.SZ',evidence_delta=2)
  w=r['watchlist_update_from_real_disclosure']
  self.assertGreater(len(w['claims_strengthened']),0)
 def test_no_pending(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'reporting'))
  from build_phase65b_watchlist_update_from_real_disclosure import build
  r=build('300308.SZ')
  w=r['watchlist_update_from_real_disclosure']
  self.assertEqual(w['pending_created'],0)
  self.assertEqual(w['paper_order_created'],0)
  self.assertEqual(w['real_trade_created'],0)
if __name__=='__main__':unittest.main()
