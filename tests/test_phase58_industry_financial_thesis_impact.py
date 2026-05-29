#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
sys.path.insert(0, '08_scripts/reporting')
from build_phase58_industry_financial_thesis_impact import build


class TestIndustryThesisImpact(unittest.TestCase):
    def test_has_7_claims(self):
        r = build(None, '300308.SZ')
        d = r['industry_financial_thesis_impact']
        self.assertEqual(d['claims_checked'], 7)

    def test_each_has_limitation(self):
        r = build(None, '300308.SZ')
        for row in r['industry_financial_thesis_impact']['rows']:
            self.assertTrue(len(row['limitation']) > 0)

    def test_no_overattribution(self):
        r = build(None, '300308.SZ')
        text = str(r)
        self.assertNotIn('证明800G', text)
        self.assertNotIn('确认ASP', text)

    def test_unconfirmed_claims(self):
        r = build(None, '300308.SZ')
        d = r['industry_financial_thesis_impact']
        self.assertGreaterEqual(d['claims_unconfirmed'], 1)


if __name__ == '__main__':
    unittest.main()
