import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestRescan(unittest.TestCase):
    def test_build(self):
        from build_phase78_688041_existing_pdf_rescan import build
        r=build();rc=r["phase78_688041_existing_pdf_rescan"]
        self.assertEqual(rc["pdfs_rescanned"],5)
    def test_legal_still_excluded(self):
        from build_phase78_688041_existing_pdf_rescan import build
        r=build();rows=r["phase78_688041_existing_pdf_rescan"]["rows"]
        for row in rows:
            if row["document_type"]=="legal_opinion":
                self.assertFalse(row["allowed_for_deep_extraction"])
    def test_new_hits(self):
        from build_phase78_688041_existing_pdf_rescan import build
        r=build();h=r["phase78_688041_existing_pdf_rescan"]["new_variable_hits"]
        self.assertGreater(sum(h.values()),0)
if __name__=="__main__":unittest.main()
