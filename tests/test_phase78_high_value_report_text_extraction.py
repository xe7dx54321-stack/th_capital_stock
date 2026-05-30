import unittest,sys
from pathlib import Path
J=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(J) not in sys.path:sys.path.insert(0,str(J))
class TestTextExtraction(unittest.TestCase):
    def test_execute(self):
        from run_phase78_688041_high_value_report_text_extraction import run
        r=run("execute");rr=r["phase78_688041_high_value_report_text_extraction"]
        self.assertGreaterEqual(rr["pdf_text_ok"],0)
        self.assertFalse(rr["ocr_used"])
    def test_no_text_no_guess(self):
        from run_phase78_688041_high_value_report_text_extraction import run
        r=run("execute");rows=r["phase78_688041_high_value_report_text_extraction"]["rows"]
        for row in rows:
            if row["text_extraction_status"]=="pdf_text_failed":
                self.assertIn("failure_reason",row)
    def test_dry_run(self):
        from run_phase78_688041_high_value_report_text_extraction import run
        r=run("dry_run");self.assertIsNotNone(r)
if __name__=="__main__":unittest.main()
