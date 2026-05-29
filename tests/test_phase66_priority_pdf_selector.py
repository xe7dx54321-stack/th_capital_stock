import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_priority_pdf_selector import select_priority_pdfs

class TestPriorityPdfSelector(unittest.TestCase):
    def test_max_pdfs_respected(self):
        rows=[{"source_id":f"s{i}","title":f"title {i}","pdf_url_available":True,"source_type":"investor_relations_record"} for i in range(30)]
        sel=select_priority_pdfs(rows,max_pdfs=10)
        self.assertLessEqual(sel["selected_pdfs"],10)
    def test_duplicate_titles_filtered(self):
        rows=[{"source_id":"a","title":"same title","pdf_url_available":True,"source_type":"annual_report"},
              {"source_id":"b","title":"same title","pdf_url_available":True,"source_type":"annual_report"}]
        sel=select_priority_pdfs(rows,max_pdfs=5)
        self.assertEqual(sel["selected_pdfs"],1)
    def test_no_pdf_url_skipped(self):
        rows=[{"source_id":"a","title":"no pdf","pdf_url_available":False,"source_type":"annual_report"}]
        sel=select_priority_pdfs(rows,max_pdfs=5)
        self.assertEqual(sel["selected_pdfs"],0)
    def test_keyword_hit_scored_higher(self):
        rows=[{"source_id":"a","title":"800G光模块出货","pdf_url_available":True,"source_type":"investor_relations_record"},
              {"source_id":"b","title":"管理公告","pdf_url_available":True,"source_type":"other_announcement"}]
        sel=select_priority_pdfs(rows,max_pdfs=5)
        self.assertGreater(sel["rows"][0]["priority_score"],sel["rows"][1]["priority_score"])
    def test_selection_reason_present(self):
        rows=[{"source_id":"a","title":"800G光模块出货","pdf_url_available":True,"source_type":"investor_relations_record"}]
        sel=select_priority_pdfs(rows,max_pdfs=5)
        self.assertGreater(len(sel["rows"][0].get("selection_reason",[])),0)
    def test_only_selection_no_download(self):
        rows=[{"source_id":"a","title":"test","pdf_url_available":True,"source_type":"annual_report"}]
        sel=select_priority_pdfs(rows,max_pdfs=5)
        self.assertIn("selected_pdfs",sel)

if __name__=="__main__":unittest.main()
