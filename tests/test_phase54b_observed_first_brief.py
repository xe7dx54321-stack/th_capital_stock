#!/usr/bin/env python3
import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

from smr_investment_logic_brief_builder import build_investment_logic_brief
from smr_research_brief_depth_lint import lint_depth

class ObservedFirstBriefTests(unittest.TestCase):

    def test_brief_has_current_observations(self):
        brief = build_investment_logic_brief('300308.SZ')
        ib = brief['investment_logic_brief']
        self.assertIn('current_observations', ib)
        self.assertGreater(len(ib['current_observations']), 0)

    def test_brief_has_implications(self):
        brief = build_investment_logic_brief('300308.SZ')
        ib = brief['investment_logic_brief']
        self.assertIn('implications', ib)
        self.assertGreater(len(ib['implications']), 0)

    def test_brief_has_can_conclude(self):
        brief = build_investment_logic_brief('300308.SZ')
        ib = brief['investment_logic_brief']
        self.assertIn('can_conclude', ib)
        self.assertGreater(len(ib['can_conclude']), 0)

    def test_brief_has_cannot_conclude(self):
        brief = build_investment_logic_brief('300308.SZ')
        ib = brief['investment_logic_brief']
        self.assertIn('cannot_conclude', ib)
        self.assertGreater(len(ib['cannot_conclude']), 0)

    def test_cannot_conclude_uses_cannot_confirm_language(self):
        brief = build_investment_logic_brief('300308.SZ')
        ib = brief['investment_logic_brief']
        cannot = ' '.join(ib['cannot_conclude'])
        self.assertIn('不能确认', cannot)

    def test_depth_lint_observed_first_passes(self):
        brief = build_investment_logic_brief('300308.SZ')
        ib = brief['investment_logic_brief']
        full = ' '.join(ib.get('current_observations', []))
        full += ' '.join(ib.get('implications', []))
        full += ' '.join(ib.get('can_conclude', []))
        full += ' '.join(ib.get('cannot_conclude', []))
        result = lint_depth(full)
        self.assertEqual(result['depth_status'], 'pass')

    def test_depth_lint_has_observation_check(self):
        result = lint_depth('现有材料显示，需求仍然强劲。')
        self.assertTrue(result['checks']['has_current_observations'])

    def test_depth_lint_no_observation_fails(self):
        result = lint_depth('下一步重点看季报里的收入增速。')
        self.assertFalse(result['checks']['has_current_observations'])

    def test_business_variable_detail_present(self):
        brief = build_investment_logic_brief('300308.SZ')
        ib = brief['investment_logic_brief']
        self.assertIn('business_variable_detail', ib)
        self.assertGreater(len(ib['business_variable_detail']), 0)

if __name__ == '__main__':
    unittest.main()
