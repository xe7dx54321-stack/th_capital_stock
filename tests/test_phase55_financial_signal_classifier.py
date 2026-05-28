import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
class Phase55ClassifierTests(unittest.TestCase):
    def test_classification_has_observed_implications(self):
        from smr_financial_signal_classifier import classify_financial_signals
        r = classify_financial_signals()
        sc = r['financial_signal_classification']
        self.assertIn('observed_implications', sc)
        self.assertGreater(len(sc['observed_implications']), 0)
    def test_classification_not_trading_advice(self):
        import json
        from smr_financial_signal_classifier import classify_financial_signals
        r = json.dumps(classify_financial_signals(), ensure_ascii=False)
        self.assertNotIn('买入', r)
        self.assertNotIn('卖出', r)
    def test_overall_status_is_string(self):
        from smr_financial_signal_classifier import classify_financial_signals
        r = classify_financial_signals()
        sc = r['financial_signal_classification']
        self.assertIsInstance(sc['overall_status'], str)
    def test_fixture_note_present(self):
        from smr_financial_signal_classifier import classify_financial_signals
        r = classify_financial_signals()
        sc = r['financial_signal_classification']
        self.assertIn('fixture_note', sc)

if __name__ == '__main__':
    unittest.main()
