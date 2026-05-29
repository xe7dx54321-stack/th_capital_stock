#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
from smr_financial_capex_field_matcher import fuzzy_match_capex_column, find_capex_columns, match_capex_fields


class TestCapexFieldMatching(unittest.TestCase):
    def test_exact_cn_match(self):
        matched, method = fuzzy_match_capex_column('购建固定资产、无形资产和其他长期资产支付的现金')
        self.assertTrue(matched)
        self.assertEqual(method, 'exact_cn')

    def test_exact_cn_variant(self):
        matched, method = fuzzy_match_capex_column('购建固定资产、无形资产和其他长期资产所支付的现金')
        self.assertTrue(matched)

    def test_fuzzy_cn_match(self):
        # Fuzzy: contains 固定资产 and 支付 but not exact match
        matched, method = fuzzy_match_capex_column('购建固定资产无形资产和其他长期资产支付现金')
        self.assertTrue(matched)
        self.assertTrue(method in ('exact_cn', 'fuzzy_cn_keyword'))

    def test_no_match_non_capex(self):
        matched, method = fuzzy_match_capex_column('营业收入')
        self.assertFalse(matched)

    def test_no_match_disposal(self):
        matched, method = fuzzy_match_capex_column('处置固定资产、无形资产和其他长期资产支付的现金')
        self.assertFalse(matched)

    def test_no_match_empty(self):
        matched, method = fuzzy_match_capex_column('')
        self.assertFalse(matched)

    def test_no_match_none(self):
        matched, method = fuzzy_match_capex_column(None)
        self.assertFalse(matched)

    def test_find_capex_columns(self):
        cols = ['营业收入', '购建固定资产、无形资产和其他长期资产支付的现金', '净利润']
        matched = find_capex_columns(cols)
        self.assertEqual(len(matched), 1)

    def test_match_capex_fields_missing(self):
        result = match_capex_fields('300308.SZ', ['营业收入', '净利润'])
        self.assertTrue(result['capex_field_matching']['capex_missing_after_match'])
        self.assertIn('missing_reason', result['capex_field_matching'])

    def test_match_capex_fields_found(self):
        result = match_capex_fields('300308.SZ', ['购建固定资产、无形资产和其他长期资产支付的现金'])
        self.assertFalse(result['capex_field_matching']['capex_missing_after_match'])


if __name__ == '__main__':
    unittest.main()
