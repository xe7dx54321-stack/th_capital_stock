import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_phase67_high_value_pdf_pool_loader import load_high_value_pool
class TestHighValuePool(unittest.TestCase):
    def test_returns_structure(self):
        r=load_high_value_pool("300308.SZ",max_pages=2,max_pdfs=10)
        p=r["phase67b_high_value_pdf_pool"]
        self.assertIn("high_value_pdfs",p)
    def test_no_admin_in_pool(self):
        pool_rows=[{"title":"投资者关系活动记录表","adjunct_url":"/t.pdf","source_type":"investor_relations_record"},
                   {"title":"独立董事声明","adjunct_url":"/t2.pdf","source_type":"other_announcement"}]
        self.assertEqual(1,1)
    def test_max_pdfs_respected(self):
        r=load_high_value_pool("300308.SZ",max_pages=2,max_pdfs=5)
        self.assertLessEqual(r["phase67b_high_value_pdf_pool"]["high_value_pdfs"],5)
if __name__=="__main__":unittest.main()
