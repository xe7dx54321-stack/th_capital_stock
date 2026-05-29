import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_business_keyword_hit_scanner import scan_title,scan_text,load_keywords

class TestKeywordHitScanner(unittest.TestCase):
    def test_load_keywords_not_empty(self):
        kw=load_keywords()
        self.assertGreater(len(kw),0,"keywords config should have groups")
    def test_scan_title_hits_800G(self):
        ts=scan_title("800G光模块投资者关系记录")
        self.assertTrue(ts["title_hit"])
        self.assertIn("product_generation",ts["keyword_groups"])
    def test_scan_title_no_hit(self):
        ts=scan_title("日常管理公告")
        self.assertFalse(ts["title_hit"])
    def test_scan_text_hits_1_6T(self):
        ts=scan_text("公司1.6T产品已开始出货")
        self.assertTrue(ts["text_hit"])
    def test_title_hit_not_evidence_confirmed(self):
        ts=scan_title("800G产品介绍")
        self.assertTrue(ts["title_hit"])
        self.assertNotIn("confirmed",str(ts))
    def test_keyword_group_breakdown(self):
        from smr_business_keyword_hit_scanner import scan_metadata_rows
        rows=[{"source_id":"a","title":"800G光模块出货与客户需求","pdf_url_available":True}]
        result=scan_metadata_rows(rows)
        self.assertGreater(result.get("sources_with_keyword_hit",0),0)

if __name__=="__main__":unittest.main()
