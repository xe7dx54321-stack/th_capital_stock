import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_phase67b_ir_report_text_quality import classify_67b_text
class TestIRReportTextQuality(unittest.TestCase):
    def test_ir_text_scores_high(self):
        rows=[{"text_extraction_status":"pdf_text_ok","source_type":"investor_relations_record","text_length":6000,"keyword_groups_hit":["product_generation","customer_demand"],"title":"IR记录","source_id":"s1"}]
        r=classify_67b_text(rows)
        self.assertEqual(r["texts_checked"],1)
        self.assertGreater(r["texts_usable_for_deep_extraction"],0)
    def test_short_text_low_signal(self):
        rows=[{"text_extraction_status":"pdf_text_ok","source_type":"other_announcement","text_length":200,"keyword_groups_hit":[],"title":"short","source_id":"s2"}]
        r=classify_67b_text(rows)
        self.assertEqual(r["texts_checked"],1)
        self.assertIn(r["rows"][0]["quality_grade"],["low_signal","financial_report_context"])
    def test_low_signal_not_usable(self):
        rows=[{"text_extraction_status":"pdf_text_ok","source_type":"other","text_length":200,"keyword_groups_hit":[],"title":"x","source_id":"x"}]
        r=classify_67b_text(rows)
        if r["texts_checked"]>0:
            self.assertFalse(r["rows"][0].get("usable_for_deep"))
if __name__=="__main__":unittest.main()
