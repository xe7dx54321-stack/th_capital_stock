import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestDeepEvidence(unittest.TestCase):
    def test_legal_not_business(self):
        from smr_phase77_deep_pdf_evidence_extractor import extract_deep_evidence
        rows=[{"allowed_for_deep_extraction":False,"document_type":"legal_opinion","matched_variables":["governance_context"]}]
        r=extract_deep_evidence(rows)
        ev=r["phase77_688041_deep_pdf_evidence"]["rows"]
        self.assertTrue(all(e["evidence_strength"]=="weak_context" for e in ev))
    def test_supervision_generates_evidence(self):
        from smr_phase77_deep_pdf_evidence_extractor import extract_deep_evidence
        rows=[{"allowed_for_deep_extraction":True,"document_type":"supervision_report","matched_variables":["product_progress","R&D"],"reliability_score":0.78,"business_relevance":"medium"}]
        r=extract_deep_evidence(rows)
        self.assertGreater(r["phase77_688041_deep_pdf_evidence"]["deep_evidence_created"],0)
    def test_not_confirmed(self):
        from smr_phase77_deep_pdf_evidence_extractor import extract_deep_evidence
        rows=[{"allowed_for_deep_extraction":True,"document_type":"supervision_report","matched_variables":["product_progress"],"reliability_score":0.78,"business_relevance":"medium"}]
        r=extract_deep_evidence(rows)
        for row in r["phase77_688041_deep_pdf_evidence"]["rows"]:
            self.assertNotEqual(row["evidence_strength"],"confirmed")
if __name__=="__main__":unittest.main()
