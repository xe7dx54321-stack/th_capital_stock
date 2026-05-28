import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
class Phase55ThesisImpactTests(unittest.TestCase):
    def test_impact_does_not_generate_trading(self):
        import json
        from smr_financial_to_thesis_impact_mapper import map_financial_to_thesis
        r = json.dumps(map_financial_to_thesis(), ensure_ascii=False)
        self.assertNotIn('buy', r.lower())
        self.assertNotIn('sell', r.lower())
    def test_impact_has_limitations(self):
        from smr_financial_to_thesis_impact_mapper import map_financial_to_thesis
        r = map_financial_to_thesis()
        ti = r['financial_to_thesis_impact']
        for row in ti['rows']:
            self.assertIn('limitation', row)
    def test_fixture_only_low_confidence(self):
        from smr_financial_to_thesis_impact_mapper import map_financial_to_thesis
        r = map_financial_to_thesis()
        ti = r['financial_to_thesis_impact']
        self.assertIn('fixture_note', ti)
        self.assertIn('fixture', ti['fixture_note'].lower())
    def test_claims_categorized(self):
        from smr_financial_to_thesis_impact_mapper import map_financial_to_thesis
        r = map_financial_to_thesis()
        ti = r['financial_to_thesis_impact']
        self.assertIn('claims_strengthened', ti)
        self.assertIn('claims_unjudgeable', ti)

if __name__ == '__main__':
    unittest.main()
