import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestTextReplay(unittest.TestCase):
    def test_execute(self):
        from run_phase79_688041_pdf_text_extraction_replay import run
        r=run("execute");rr=r["phase79_688041_pdf_text_extraction_replay"]
        self.assertEqual(rr["pdf_text_ok"],3)
        self.assertFalse(rr["ocr_used"])
    def test_encrypted_detected(self):
        from run_phase79_688041_pdf_text_extraction_replay import run
        r=run("execute");rows=r["phase79_688041_pdf_text_extraction_replay"]["rows"]
        enc=[r for r in rows if r.get("encrypted_pdf")];self.assertGreater(len(enc),0)
    def test_text_hash_present(self):
        from run_phase79_688041_pdf_text_extraction_replay import run
        r=run("execute");rows=r["phase79_688041_pdf_text_extraction_replay"]["rows"]
        for row in rows:
            if row["text_extraction_status"]=="pdf_text_ok":self.assertTrue(len(row.get("text_hash",""))>0)
if __name__=="__main__":unittest.main()
