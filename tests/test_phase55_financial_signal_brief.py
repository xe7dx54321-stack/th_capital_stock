import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
class Phase55BriefTests(unittest.TestCase):
    def test_brief_has_observed_first_structure(self):
        from smr_financial_signal_classifier import classify_financial_signals
        from smr_financial_source_availability import check_financial_source_availability
        avail = check_financial_source_availability()
        self.assertIn('financial_source_availability', avail)
    def test_brief_no_teaching_style(self):
        import json
        from smr_financial_signal_classifier import classify_financial_signals
        r = json.dumps(classify_financial_signals(), ensure_ascii=False)
        self.assertNotIn('下一步重点看', r)
        self.assertNotIn('建议关注', r)
    def test_brief_marks_fixture(self):
        from smr_financial_signal_classifier import classify_financial_signals
        r = classify_financial_signals()
        sc = r['financial_signal_classification']
        self.assertIn('fixture_note', sc)

if __name__ == '__main__':
    unittest.main()
