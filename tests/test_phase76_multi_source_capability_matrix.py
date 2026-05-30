import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestMultiSourceMatrix(unittest.TestCase):
    def test_build(self):
        from build_phase76_multi_source_capability_matrix import build
        r = build()
        m = r["phase76_multi_source_capability_matrix"]
        self.assertEqual(m["tickers_checked"], 3)
    def test_pdf_not_written_as_text(self):
        from build_phase76_multi_source_capability_matrix import build
        r = build()
        for row in r["phase76_multi_source_capability_matrix"]["rows"]:
            if "cninfo_pdf_download" in row:
                self.assertNotEqual(row.get("cninfo_pdf_download"), "text_available")

if __name__ == "__main__": unittest.main()
