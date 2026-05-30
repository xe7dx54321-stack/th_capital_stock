import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestNormalizer(unittest.TestCase):
    def test_normalize_unicode(self):
        from smr_phase78_chinese_keyword_normalizer import normalize_text
        self.assertIn("研发",normalize_text("研发投入"))
    def test_full_width(self):
        from smr_phase78_chinese_keyword_normalizer import normalize_text
        self.assertIn("ABC",normalize_text("ＡＢＣ"))
    def test_chinese_punctuation(self):
        from smr_phase78_chinese_keyword_normalizer import normalize_text
        n=normalize_text("产品，芯片。")
        self.assertIn("产品",n)
    def test_casefold(self):
        from smr_phase78_chinese_keyword_normalizer import casefold_english
        self.assertEqual(casefold_english("R&D"),"r&d")
    def test_context_window(self):
        from smr_phase78_chinese_keyword_normalizer import extract_context_window
        c=extract_context_window("公司营业收入大幅增长","营业收入")
        self.assertIn("营业收入",c)
    def test_negative_exclusion(self):
        from smr_phase78_chinese_keyword_normalizer import match_with_negatives
        h=match_with_negatives("股东大会审议通过产品议案",["产品"],["股东大会"])
        self.assertEqual(len(h),0)
    def test_no_negatives_needed(self):
        from smr_phase78_chinese_keyword_normalizer import match_with_negatives
        h=match_with_negatives("公司产品竞争力强",["产品"],["股东大会"])
        self.assertEqual(len(h),1)
if __name__=="__main__":unittest.main()
