#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
from smr_cumulative_to_quarterly_converter import convert_cumulative_to_single_quarter


class TestSingleQuarterConversion(unittest.TestCase):
    def setUp(self):
        self.basic_cum = [
            {'period': '2024Q1', 'period_type': 'cumulative', 'metric': 'revenue', 'value': 100},
            {'period': '2024Q2', 'period_type': 'cumulative', 'metric': 'revenue', 'value': 250},
            {'period': '2024Q3', 'period_type': 'cumulative', 'metric': 'revenue', 'value': 400},
            {'period': '2024Q4', 'period_type': 'cumulative', 'metric': 'revenue', 'value': 600},
            {'period': '2024Q1', 'period_type': 'cumulative', 'metric': 'net_profit', 'value': 20},
            {'period': '2024Q2', 'period_type': 'cumulative', 'metric': 'net_profit', 'value': 55},
            {'period': '2024Q3', 'period_type': 'cumulative', 'metric': 'net_profit', 'value': 90},
            {'period': '2024Q4', 'period_type': 'cumulative', 'metric': 'net_profit', 'value': 140},
        ]

    def test_q1_identity(self):
        result = convert_cumulative_to_single_quarter(self.basic_cum)
        q1_rev = next(r for r in result['single_quarter_records'] if r['period'] == '2024Q1' and r['metric'] == 'revenue')
        self.assertEqual(q1_rev['value'], 100)
        self.assertEqual(q1_rev['derivation'], 'q1_identity')

    def test_q2_minus_q1(self):
        result = convert_cumulative_to_single_quarter(self.basic_cum)
        q2_rev = next(r for r in result['single_quarter_records'] if r['period'] == '2024Q2' and r['metric'] == 'revenue')
        self.assertEqual(q2_rev['value'], 150)
        self.assertEqual(q2_rev['derivation'], 'q2_minus_q1')

    def test_q3_minus_q2(self):
        result = convert_cumulative_to_single_quarter(self.basic_cum)
        q3_rev = next(r for r in result['single_quarter_records'] if r['period'] == '2024Q3' and r['metric'] == 'revenue')
        self.assertEqual(q3_rev['value'], 150)
        self.assertEqual(q3_rev['derivation'], 'q3_minus_q2')

    def test_q4_minus_q3(self):
        result = convert_cumulative_to_single_quarter(self.basic_cum)
        q4_rev = next(r for r in result['single_quarter_records'] if r['period'] == '2024Q4' and r['metric'] == 'revenue')
        self.assertEqual(q4_rev['value'], 200)
        self.assertEqual(q4_rev['derivation'], 'q4_minus_q3')

    def test_balance_sheet_skipped(self):
        records = self.basic_cum + [
            {'period': '2024Q1', 'period_type': 'cumulative', 'metric': 'inventory', 'value': 500},
        ]
        result = convert_cumulative_to_single_quarter(records)
        self.assertIn('inventory', result['balance_sheet_metrics_skipped'])
        # No single-quarter inventory record
        sq_metrics = set(r['metric'] for r in result['single_quarter_records'])
        self.assertNotIn('inventory', sq_metrics)

    def test_missing_cumulative_warning(self):
        records = [
            {'period': '2024Q2', 'period_type': 'cumulative', 'metric': 'revenue', 'value': 250},
        ]
        result = convert_cumulative_to_single_quarter(records)
        self.assertTrue(any('missing Q1' in w for w in result['conversion_warnings']))

    def test_conversion_net_profit(self):
        result = convert_cumulative_to_single_quarter(self.basic_cum)
        q2_np = next(r for r in result['single_quarter_records'] if r['period'] == '2024Q2' and r['metric'] == 'net_profit')
        self.assertEqual(q2_np['value'], 35)
        q4_np = next(r for r in result['single_quarter_records'] if r['period'] == '2024Q4' and r['metric'] == 'net_profit')
        self.assertEqual(q4_np['value'], 50)

    def test_derived_label(self):
        result = convert_cumulative_to_single_quarter(self.basic_cum)
        for r in result['single_quarter_records']:
            self.assertEqual(r['period_type'], 'single_quarter')
            self.assertEqual(r['derived_from'], 'cumulative')
            self.assertIn(r['derivation'], ['q1_identity', 'q2_minus_q1', 'q3_minus_q2', 'q4_minus_q3'])

    def test_empty_records(self):
        result = convert_cumulative_to_single_quarter([])
        self.assertEqual(result['single_quarter_records_created'], 0)


if __name__ == '__main__':
    unittest.main()
