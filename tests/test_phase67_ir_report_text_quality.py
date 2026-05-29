import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_ir_report_text_quality_classifier import classify_ir_report_text, classify_texts
class TestIRReportTextQuality(unittest.TestCase):
    def test_ir_record_scores_high(self):
        q=classify_ir_report_text("投资者关系活动记录表","investor_relations_record",6000,["product_generation","customer_demand"])
        self.assertIn(q["quality_grade"],["high_signal_ir_text","usable_ir_text"])
    def test_admin_text_detected(self):
        q=classify_ir_report_text("独立董事声明","other_announcement",2000,[])
        self.assertIn(q["quality_grade"],["administrative_text","low_signal","rejected"])
    def test_low_signal_not_usable_for_deep(self):
        q=classify_ir_report_text("日常公告","other_announcement",500,[])
        self.assertFalse(q["usable_for_deep"])
    def test_classify_texts_batch(self):
        rows=[{"text_extraction_status":"pdf_text_ok","title":"IR记录","source_type":"investor_relations_record","text_length":5000,"keyword_groups_hit":["product_generation"]}]
        result=classify_texts(rows)
        self.assertEqual(result["texts_checked"],1)
    def test_report_text_scores(self):
        q=classify_ir_report_text("年度报告","annual_report",8000,[])
        self.assertIn(q["quality_grade"],["usable_report_text","financial_report_context","usable_ir_text"])
if __name__=="__main__":unittest.main()
