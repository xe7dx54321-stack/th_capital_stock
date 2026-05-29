#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
from smr_financial_signal_to_industry_variable_mapper import map_signals_to_industry_variables


class TestSignalToIndustryMap(unittest.TestCase):
    def test_maps_6_variables(self):
        r = map_signals_to_industry_variables('300308.SZ')
        d = r['financial_signal_to_industry_variable_map']
        self.assertGreaterEqual(d['industry_variables_mapped'], 6)

    def test_each_row_has_cannot_conclude(self):
        r = map_signals_to_industry_variables('300308.SZ')
        for row in r['financial_signal_to_industry_variable_map']['rows']:
            self.assertIn('cannot_conclude', row)
            self.assertGreater(len(row['cannot_conclude']), 0)

    def test_each_row_has_status(self):
        r = map_signals_to_industry_variables('300308.SZ')
        valid = ['supported_by_financial_signal', 'partially_supported',
                 'weakened_by_financial_signal', 'not_observable_from_financials']
        for row in r['financial_signal_to_industry_variable_map']['rows']:
            self.assertIn(row['variable_status'], valid)

    def test_no_800g_claim_as_conclusion(self):
        r = map_signals_to_industry_variables('300308.SZ')
        text = json.dumps(r)
        self.assertNotIn('证明800G', str(text))
        self.assertNotIn('证明1.6T', str(text))


import json
if __name__ == '__main__':
    unittest.main()
