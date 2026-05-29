#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class T(unittest.TestCase):
 def test_300308_has_org_id(self):
  from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
  self.assertEqual(CURATED_CNINFO_IDENTITIES["300308.SZ"]["org_id"],"9900022016")
 def test_stock_param_format(self):
  from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
  c=CURATED_CNINFO_IDENTITIES["300308.SZ"]
  sp=c["security_code"]+","+c["org_id"]
  self.assertEqual(sp,"300308,9900022016")
 def test_ticker_specific(self):
  from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
  self.assertIn("300308.SZ",CURATED_CNINFO_IDENTITIES)
  self.assertNotIn("999999.SZ",CURATED_CNINFO_IDENTITIES)
if __name__=="__main__":unittest.main()
