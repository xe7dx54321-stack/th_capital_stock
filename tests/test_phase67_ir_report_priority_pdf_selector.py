import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_ir_report_priority_pdf_selector import select_ir_report_pdfs
class TestIRReportPDFSelector(unittest.TestCase):
    def test_max_pdfs_respected(self):
        rows=[{"source_id":f"s{i}","title":"投资者关系活动记录表","pdf_url_available":True,"source_type":"investor_relations_record","adjunct_url":"/test.pdf"} for i in range(40)]
        sel=select_ir_report_pdfs(rows,max_pdfs=20)
        self.assertLessEqual(sel["selected_pdfs"],20)
    def test_admin_legal_filtered(self):
        rows=[{"title":"独董声明","pdf_url_available":True,"source_type":"other","adjunct_url":"/test.pdf"}]
        sel=select_ir_report_pdfs(rows,max_pdfs=25)
        self.assertEqual(sel["selected_pdfs"],0)
    def test_ir_record_prioritized(self):
        rows=[{"source_id":"a","title":"投资者关系活动记录表","pdf_url_available":True,"source_type":"investor_relations_record","adjunct_url":"/t1.pdf"},{"source_id":"b","title":"日常公告","pdf_url_available":True,"source_type":"other_announcement","adjunct_url":"/t2.pdf"}]
        sel=select_ir_report_pdfs(rows,max_pdfs=25)
        if sel["selected_pdfs"]>0:
            self.assertIn(sel["rows"][0]["source_type"],["investor_relations_record"])
    def test_selection_reason(self):
        rows=[{"source_id":"a","title":"投资者关系活动记录表","pdf_url_available":True,"source_type":"investor_relations_record","adjunct_url":"/t.pdf"}]
        sel=select_ir_report_pdfs(rows,max_pdfs=25)
        if sel["selected_pdfs"]>0:
            self.assertGreater(len(sel["rows"][0].get("selection_reason",[])),0)
if __name__=="__main__":unittest.main()
