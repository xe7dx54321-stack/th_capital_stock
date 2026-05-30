import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Test688041PDFInventory(unittest.TestCase):
    def test_build_empty(self):
        from smr_phase76_688041_pdf_inventory import build_inventory
        r = build_inventory("688041.SH", [])
        inv = r["phase76_688041_pdf_inventory"]
        self.assertEqual(inv["ticker"], "688041.SH")
        self.assertEqual(inv["pdf_candidates_selected"], 0)
    def test_identity_not_found(self):
        from smr_phase76_688041_pdf_inventory import build_inventory
        r = build_inventory("000000.XY", [])
        inv = r["phase76_688041_pdf_inventory"]
        self.assertEqual(inv["status"], "identity_not_found")
    def test_annual_report_p0(self):
        from smr_phase76_688041_pdf_inventory import classify_category
        cat, rank = classify_category(u"2024年年度报告")
        self.assertEqual(cat, "annual_report")
        self.assertEqual(rank, 0)
    def test_admin_downgraded(self):
        from smr_phase76_688041_pdf_inventory import classify_category
        cat, rank = classify_category(u"股权激励计划")
        self.assertIn("admin", cat)
        self.assertGreater(rank, 50)

if __name__ == "__main__": unittest.main()
