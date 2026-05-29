#!/usr/bin/env python3
import unittest, sys, json
sys.path.insert(0, '08_scripts/lib')
sys.path.insert(0, '08_scripts/reporting')
from build_phase57_quarterly_metric_coverage import build


class TestQuarterlyMetricCoverage(unittest.TestCase):
    def test_coverage_for_300308(self):
        result = build(None, '300308.SZ')
        d = result['quarterly_metric_coverage']
        self.assertGreater(d['periods_checked'], 0)
        self.assertTrue(len(d['latest_period']) > 0)
        self.assertIsInstance(d['metrics_covered'], list)
        self.assertIsInstance(d['metrics_missing'], list)
        self.assertIn('revenue', d['metrics_covered'] or [])

    def test_coverage_has_required_fields(self):
        result = build(None, '300308.SZ')
        d = result['quarterly_metric_coverage']
        for key in ['periods_checked', 'latest_period', 'metrics_covered',
                     'metrics_missing', 'single_quarter_available',
                     'cumulative_available', 'balance_sheet_period_end_available']:
            self.assertIn(key, d)


if __name__ == '__main__':
    unittest.main()
