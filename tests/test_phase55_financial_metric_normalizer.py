import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
class Phase55NormalizerTests(unittest.TestCase):
    def test_normalizer_does_not_change_values(self):
        from smr_financial_metric_normalizer import normalize_financial_metrics
        from smr_financial_statement_loader import load_financial_statements
        ld = load_financial_statements()['financial_statement_loader']
        orig = {r['period']+'_'+r['metric']: r['value'] for r in ld['records']}
        nm = normalize_financial_metrics()['financial_metric_normalization']
        for row in nm['rows']:
            key = row['period']+'_'+row['metric']
            if key in orig:
                self.assertEqual(row['value'], orig[key])
    def test_missing_metrics_reported(self):
        from smr_financial_metric_normalizer import normalize_financial_metrics
        nm = normalize_financial_metrics()['financial_metric_normalization']
        self.assertIn('missing_metrics', nm)
        self.assertGreater(len(nm['missing_metrics']), 0)
    def test_fixture_confidence_marked(self):
        from smr_financial_metric_normalizer import normalize_financial_metrics
        nm = normalize_financial_metrics()['financial_metric_normalization']
        for row in nm['rows']:
            self.assertEqual(row['confidence'], 'fixture_only')

if __name__ == '__main__':
    unittest.main()
