import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_administrative_disclosure_filter import is_administrative_or_legal, filter_disclosures
class TestAdminFilter(unittest.TestCase):
    def test_detects_equity_incentive(self):
        self.assertTrue(is_administrative_or_legal("关于调整限制性股票归属价格的公告"))
    def test_detects_independent_director(self):
        self.assertTrue(is_administrative_or_legal("独立董事候选人声明与承诺"))
    def test_detects_legal_opinion(self):
        self.assertTrue(is_administrative_or_legal("律师事务所法律意见书"))
    def test_non_admin_passes(self):
        self.assertFalse(is_administrative_or_legal("投资者关系活动记录表"))
    def test_归属价格_not_product_asp(self):
        rows=[{"title":"关于调整限制性股票归属价格的公告","source_type":"other"}]
        fr=filter_disclosures(rows)
        self.assertGreater(fr["filtered_out"],0)
    def test_filter_counts(self):
        rows=[{"title":"独立董事声明","source_type":"other"},{"title":"投资者关系活动记录","source_type":"investor_relations_record"}]
        fr=filter_disclosures(rows)
        self.assertEqual(fr["metadata_checked"],2)
        self.assertGreater(fr["administrative_or_legal_detected"],0)
        self.assertGreater(fr["business_disclosures_retained"],0)
if __name__=="__main__":unittest.main()
