import unittest,sys
from pathlib import Path
M=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(M) not in sys.path:sys.path.insert(0,str(M))
class TestChineseMatching(unittest.TestCase):
    def test_build(self):
        from build_phase78_business_relevance_chinese_matching_report import build
        r=build();m=r["phase78_business_relevance_chinese_matching"]
        self.assertGreaterEqual(m["variables_checked"],9)
        self.assertTrue(m["keyword_hit_not_confirmed"])
    def test_legal_low(self):
        from build_phase78_business_relevance_chinese_matching_report import build
        r=build();rows=r["phase78_business_relevance_chinese_matching"]["rows"]
        for row in rows:
            if row.get("document_type")=="legal_opinion":
                self.assertEqual(row["business_relevance"],"low")
                self.assertFalse(row["allowed_for_deep_extraction"])
    def test_negative_exclusions(self):
        from build_phase78_business_relevance_chinese_matching_report import build
        r=build();m=r["phase78_business_relevance_chinese_matching"]
        self.assertTrue(m["negative_exclusions_applied"])
if __name__=="__main__":unittest.main()
