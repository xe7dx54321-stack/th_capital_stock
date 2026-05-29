#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/'08_scripts'/'lib'
if str(L) not in sys.path: sys.path.insert(0,str(L))
class T(unittest.TestCase):
 def test_metadata_only(self):
  from smr_real_disclosure_text_quality_classifier import classify_text
  r=classify_text('test','title',None)
  self.assertEqual(r['quality_status'],'metadata_only_not_evidence')
 def test_too_short(self):
  from smr_real_disclosure_text_quality_classifier import classify_text
  r=classify_text('test','title','short')
  self.assertEqual(r['quality_status'],'too_short_not_evidence')
 def test_usable_with_keywords(self):
  from smr_real_disclosure_text_quality_classifier import classify_text
  text='800G光模块产品出货量持续增长'*20
  r=classify_text('test','IR记录',text)
  self.assertEqual(r['quality_status'],'usable_for_business_evidence')
if __name__=='__main__':unittest.main()
