import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestBusinessRelevance(unittest.TestCase):
    def test_legal_opinion_low(self):
        from smr_phase77_pdf_business_relevance import score_business_relevance
        rows=[{"document_type":"legal_opinion","title":"test","text_preview":""}]
        r=score_business_relevance(rows)
        rr=r["phase77_688041_business_relevance"]["rows"][0]
        self.assertEqual(rr["business_relevance"],"low")
        self.assertFalse(rr["allowed_for_deep_extraction"])
    def test_shareholder_low(self):
        from smr_phase77_pdf_business_relevance import score_business_relevance
        rows=[{"document_type":"shareholder_meeting_resolution","title":"test","text_preview":""}]
        r=score_business_relevance(rows)
        rr=r["phase77_688041_business_relevance"]["rows"][0]
        self.assertFalse(rr["allowed_for_deep_extraction"])
    def test_supervision_medium(self):
        from smr_phase77_pdf_business_relevance import score_business_relevance
        rows=[{"document_type":"supervision_report","title":"test","text_preview":""}]
        r=score_business_relevance(rows)
        rr=r["phase77_688041_business_relevance"]["rows"][0]
        self.assertTrue(rr["allowed_for_deep_extraction"])
if __name__=="__main__":unittest.main()
