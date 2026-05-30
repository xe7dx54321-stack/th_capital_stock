import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestHTMLTextQuality(unittest.TestCase):
 def test_empty_rejected(self):
  from smr_phase74_html_text_quality_classifier import classify_html_text
  r=classify_html_text("test","irm_html","");self.assertEqual(r["quality_grade"],"rejected")
 def test_irm_qa_commentary(self):
  from smr_phase74_html_text_quality_classifier import classify_html_text
  r=classify_html_text("test","irm_html","公司业务进展顺利客户需求旺盛")
  self.assertEqual(r["allowed_usage"],"management_commentary")
 def test_sse_link_only(self):
  from smr_phase74_html_text_quality_classifier import classify_html_text
  r=classify_html_text("test","sse_html","short text",link_count=10)
  self.assertEqual(r["quality_grade"],"link_only_page")
 def test_company_not_strong(self):
  from smr_phase74_html_text_quality_classifier import classify_html_text
  r=classify_html_text("test","company_ir_page","公司业务介绍及产品线说明，光模块和光器件为主要产品")
  self.assertNotEqual(r["allowed_usage"],"strong_direct")
if __name__=="__main__":unittest.main()
