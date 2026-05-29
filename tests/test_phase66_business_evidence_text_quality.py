import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_business_evidence_text_quality_scoring import score_text_quality,score_texts

class TestTextQuality(unittest.TestCase):
    def test_under_100_chars_rejected(self):
        q=score_text_quality("short","other")
        self.assertEqual(q["quality_grade"],"rejected")
    def test_high_business_relevance_scores_high(self):
        text="800G光模块 出货 交付 客户需求 订单 能见度 产能 扩产 1.6T 硅光 " * 200
        q=score_text_quality(text,"investor_relations_record")
        self.assertIn(q["quality_grade"],["high_business_signal","usable_business_signal"])
    def test_financial_only_downgraded(self):
        text="营业收入 营业成本 净利润 归属于母公司 基本每股收益 加权平均 " * 200
        q=score_text_quality(text,"annual_report")
        self.assertIn(q["quality_grade"],["financial_context_only","low_signal","rejected"])
    def test_low_signal_filtered(self):
        text="公司日常管理公告" * 50
        q=score_text_quality(text,"other_announcement")
        self.assertIn(q["quality_grade"],["low_signal","rejected"])
    def test_score_texts_batch(self):
        texts=[{"text":"800G出货客户需求产能扩产"*100,"source_type":"investor_relations_record","source_id":"a","title":"IR"},
               {"text":"short","source_type":"other","source_id":"b","title":"bad"}]
        result=score_texts(texts)
        self.assertEqual(result["texts_checked"],2)
        self.assertGreater(result.get("rejected",0),0)

if __name__=="__main__":unittest.main()
