import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestTextQuality(unittest.TestCase):
 def test_empty_rejected(self):
  from smr_phase73_fallback_text_quality import classify_fallback_text
  r=classify_fallback_text("test","irm","");self.assertEqual(r["quality_grade"],"rejected")
 def test_short_text(self):
  from smr_phase73_fallback_text_quality import classify_fallback_text
  r=classify_fallback_text("test","irm","ab");self.assertEqual(r["quality_grade"],"text_too_short")
 def test_meta_not_usable(self):
  from smr_phase73_fallback_text_quality import classify_fallback_text
  r=classify_fallback_text("test","company_ir_page","title: code: announcement:");self.assertEqual(r["quality_grade"],"metadata_only")
 def test_irm_management_commentary(self):
  from smr_phase73_fallback_text_quality import classify_fallback_text
  r=classify_fallback_text("test","irm","公司业务进展顺利")
  self.assertEqual(r["allowed_usage"],"management_commentary")
 def test_company_context_not_strong(self):
  from smr_phase73_fallback_text_quality import classify_fallback_text
  r=classify_fallback_text("test","company_ir_page","公司业务介绍，产品线包括光模块和光器件")
  self.assertNotEqual(r["allowed_usage"],"strong_direct")
if __name__=="__main__":unittest.main()
