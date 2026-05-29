import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Phase56CninfoTests(unittest.TestCase):
    def test_no_raw_content_saved(self):
        from smr_cninfo_financial_report_text_adapter import fetch_cninfo_financial_report_text
        r = fetch_cninfo_financial_report_text()
        cf = r['cninfo_financial_report_text_fetch']
        self.assertFalse(cf['raw_content_saved'])
    def test_no_ocr_used(self):
        from smr_cninfo_financial_report_text_adapter import fetch_cninfo_financial_report_text
        r = fetch_cninfo_financial_report_text()
        cf = r['cninfo_financial_report_text_fetch']
        self.assertFalse(cf['ocr_used'])

if __name__ == '__main__':
    unittest.main()
