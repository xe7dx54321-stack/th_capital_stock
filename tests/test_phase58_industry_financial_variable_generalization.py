#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
sys.path.insert(0, '08_scripts/reporting')
from build_phase58_industry_financial_variable_generalization import build


class TestGeneralization(unittest.TestCase):
    def test_has_all_layers(self):
        r = build(None)
        d = r['industry_financial_variable_generalization']
        self.assertGreater(len(d['generic_financial_framework']), 0)
        self.assertGreater(len(d['industry_specific_template']), 0)
        self.assertGreater(len(d['not_assumed_to_generalize']), 0)

    def test_not_claim_all_tickers(self):
        r = build(None)
        text = str(r)
        self.assertNotIn('所有股票', text)


if __name__ == '__main__':
    unittest.main()
