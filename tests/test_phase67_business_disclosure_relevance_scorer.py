import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_business_disclosure_relevance_scorer import score_disclosure, score_disclosures
class TestRelevanceScorer(unittest.TestCase):
    def test_ir_record_scores_high(self):
        s=score_disclosure("投资者关系活动记录表","investor_relations_record",True)
        self.assertGreater(s["relevance_score"],60)
    def test_admin_penalized(self):
        s=score_disclosure("独立董事声明","other_announcement",True)
        self.assertLess(s["relevance_score"],50)
    def test_pdf_bonus(self):
        with_pdf=score_disclosure("test","annual_report",True)
        without_pdf=score_disclosure("test","annual_report",False)
        self.assertGreater(with_pdf["relevance_score"],without_pdf["relevance_score"])
    def test_score_disclosures_batch(self):
        rows=[{"title":"投资者关系活动记录","source_type":"investor_relations_record","pdf_url_available":True},{"title":"独董声明","source_type":"other","pdf_url_available":True}]
        sc=score_disclosures(rows)
        self.assertEqual(sc["disclosures_scored"],2)
    def test_relevance_reason_present(self):
        s=score_disclosure("800G光模块出货","investor_relations_record",True)
        self.assertGreater(len(s.get("relevance_reasons",[])),0)
if __name__=="__main__":unittest.main()
