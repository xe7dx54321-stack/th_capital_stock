#!/usr/bin/env python3
import unittest, sys, json
sys.path.insert(0, '08_scripts/lib')
from smr_ai_optical_financial_variable_schema import load_ai_optical_financial_variable_schema, get_industry_variables, get_forbidden_attributions


class TestAIOpticalSchema(unittest.TestCase):
    def test_schema_loads(self):
        schema = load_ai_optical_financial_variable_schema()
        self.assertEqual(schema['industry'], 'ai_optical_module')

    def test_at_least_6_variables(self):
        variables = get_industry_variables()
        self.assertGreaterEqual(len(variables), 6)

    def test_each_variable_has_related_metrics(self):
        for v in get_industry_variables():
            self.assertIn('related_financial_metrics', v)
            self.assertGreater(len(v['related_financial_metrics']), 0)

    def test_each_variable_has_cannot_conclude(self):
        for v in get_industry_variables():
            self.assertIn('cannot_conclude_from_financials_alone', v)
            self.assertGreater(len(v['cannot_conclude_from_financials_alone']), 0)

    def test_forbidden_attributions(self):
        forbidden = get_forbidden_attributions()
        self.assertGreaterEqual(len(forbidden), 5)

    def test_no_800g_claim_as_conclusion(self):
        forbidden = get_forbidden_attributions()
        text = str(forbidden)
        self.assertIn('800G', text)


if __name__ == '__main__':
    unittest.main()
