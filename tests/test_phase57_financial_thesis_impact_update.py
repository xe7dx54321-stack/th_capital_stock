#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
sys.path.insert(0, '08_scripts/reporting')
from build_phase57_financial_thesis_impact_update import build


class TestFinancialThesisImpactUpdate(unittest.TestCase):
    def test_impact_for_300308(self):
        result = build(None, '300308.SZ')
        d = result['financial_thesis_impact_update']
        self.assertEqual(d['claims_checked'], 7)
        self.assertGreaterEqual(d['claims_strengthened'] + d['claims_weakened'] +
                                d['claims_unchanged'] + d['claims_unjudgeable'], 6)

    def test_each_claim_has_evidence(self):
        result = build(None, '300308.SZ')
        d = result['financial_thesis_impact_update']
        for row in d['rows']:
            self.assertIn('evidence', row)
            self.assertIn('limitation', row)
            self.assertTrue(len(row['evidence']) > 0)
            self.assertTrue(len(row['limitation']) > 0)

    def test_no_trade_signals(self):
        result = build(None, '300308.SZ')
        d = result['financial_thesis_impact_update']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)

    def test_impact_not_overattributing(self):
        result = build(None, '300308.SZ')
        d = result['financial_thesis_impact_update']
        text = str(d)
        self.assertNotIn('ASP', text)

    def test_limitation_present(self):
        result = build(None, '300308.SZ')
        d = result['financial_thesis_impact_update']
        for row in d['rows']:
            self.assertNotEqual(row['limitation'], '')


if __name__ == '__main__':
    unittest.main()
