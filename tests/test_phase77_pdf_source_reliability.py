import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestSourceReliability(unittest.TestCase):
    def test_supervision_above_legal(self):
        from smr_phase77_quality_config import get_reliability
        self.assertGreater(get_reliability("supervision_report"),get_reliability("legal_opinion"))
    def test_annual_above_supervision(self):
        from smr_phase77_quality_config import get_reliability
        self.assertGreater(get_reliability("annual_report"),get_reliability("supervision_report"))
    def test_score_pdfs(self):
        from smr_phase77_pdf_source_reliability import score_pdfs
        rows=[{"document_type":"legal_opinion","title":"test1"},{"document_type":"supervision_report","title":"test2"}]
        r=score_pdfs(rows)
        self.assertEqual(r["phase77_688041_source_reliability"]["pdfs_scored"],2)
if __name__=="__main__":unittest.main()
