import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L)), json
class Phase55GenTests(unittest.TestCase):
    def test_generic_capabilities_listed(self):
        from smr_financial_signal_classifier import classify_financial_signals
        r = classify_financial_signals()
        sc = r['financial_signal_classification']
        self.assertIsNotNone(sc['overall_status'])
    def test_does_not_claim_auto_generalization(self):
        from smr_financial_signal_classifier import classify_financial_signals
        r = json.dumps(classify_financial_signals(), ensure_ascii=False)
        self.assertNotIn('automatically generalizes', r)
    def test_fixture_data_clearly_labeled(self):
        from smr_financial_signal_classifier import classify_financial_signals
        r = classify_financial_signals()
        sc = r['financial_signal_classification']
        self.assertIn('fixture_note', sc)

if __name__ == '__main__':
    unittest.main()
