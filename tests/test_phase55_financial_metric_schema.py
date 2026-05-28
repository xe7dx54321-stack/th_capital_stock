import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Phase55SchemaTests(unittest.TestCase):
    def test_schema_covers_three_statements(self):
        from smr_financial_metric_schema import load_schema
        s = load_schema()
        groups = s.get('metric_groups', {})
        self.assertIn('income_statement', groups)
        self.assertIn('balance_sheet', groups)
        self.assertIn('cash_flow', groups)

    def test_schema_has_calculated_metrics(self):
        from smr_financial_metric_schema import get_calculated_metrics
        cm = get_calculated_metrics()
        self.assertIn('yoy_growth', cm)
        self.assertIn('gross_margin', cm)

    def test_schema_has_industry_extension(self):
        from smr_financial_metric_schema import load_schema
        s = load_schema()
        self.assertIn('industry_template_extension_points', s)

if __name__ == '__main__':
    unittest.main()
