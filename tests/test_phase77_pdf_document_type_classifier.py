import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestDocTypeClassifier(unittest.TestCase):
    def test_legal_opinion(self):
        from smr_phase77_pdf_document_type_classifier import classify_document
        r=classify_document(title=u"法律意见书")
        self.assertEqual(r["document_type"],"legal_opinion")
    def test_shareholder_resolution(self):
        from smr_phase77_pdf_document_type_classifier import classify_document
        r=classify_document(title=u"股东会决议公告")
        self.assertEqual(r["document_type"],"shareholder_meeting_resolution")
    def test_supervision_report(self):
        from smr_phase77_pdf_document_type_classifier import classify_document
        r=classify_document(title=u"持续督导跟踪报告")
        self.assertEqual(r["document_type"],"supervision_report")
    def test_unknown(self):
        from smr_phase77_pdf_document_type_classifier import classify_document
        r=classify_document(title="something random")
        self.assertEqual(r["document_type"],"unknown")
    def test_classify_5_pdfs(self):
        from smr_phase77_pdf_document_type_classifier import classify_pdfs
        pdfs=[{"title":u"法律意见书"},{"title":u"股东会决议"},{"title":u"督导报告"},{"title":u"保荐总结"},{"title":"unknown"}]
        r=classify_pdfs(pdfs)
        self.assertEqual(r["phase77_688041_pdf_document_type"]["pdfs_checked"],5)
if __name__=="__main__":unittest.main()
