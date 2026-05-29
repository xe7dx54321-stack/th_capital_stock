#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/'08_scripts'/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
class T(unittest.TestCase):
 def test_skip_network(self):
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'08_scripts'/'reporting'))
  from build_phase65b_cninfo_real_pdf_url_inventory import build
  r=build('300308.SZ',skip=True)
  self.assertEqual(r['cninfo_real_pdf_url_inventory']['status'],'skipped_network_disabled')
if __name__=='__main__':unittest.main()
