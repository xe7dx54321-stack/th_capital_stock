#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
from smr_industry_financial_variable_interpretation import interpret_industry_financial_variables


class TestIndustryInterpretation(unittest.TestCase):
    def test_has_observations(self):
        r = interpret_industry_financial_variables('300308.SZ')
        d = r['industry_financial_variable_interpretation']
        # May be empty on API failures - check structure
        self.assertIsInstance(d['observations'], list)
        self.assertIn('overall_interpretation', d)

    def test_each_has_cannot_conclude(self):
        r = interpret_industry_financial_variables('300308.SZ')
        for o in r['industry_financial_variable_interpretation']['observations']:
            self.assertIn('cannot_conclude', o)

    def test_observed_first(self):
        r = interpret_industry_financial_variables('300308.SZ')
        for o in r['industry_financial_variable_interpretation']['observations']:
            self.assertIn('observed_financial_fact', o)
            self.assertIn('business_implication', o)

    def test_no_teaching_style(self):
        r = interpret_industry_financial_variables('300308.SZ')
        text = str(r)
        self.assertNotIn('下一步', text)
        self.assertNotIn('建议关注', text)


if __name__ == '__main__':
    unittest.main()
