import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Phase56RegTests(unittest.TestCase):
    def test_registry_has_sources(self):
        from smr_real_financial_source_registry import load_registry
        r = load_registry()
        self.assertIn('sources', r)
        self.assertGreater(len(r['sources']), 0)
    def test_fixture_not_marked_real(self):
        from smr_real_financial_source_registry import load_registry
        r = load_registry()
        fixtures = [s for s in r['sources'] if s['confidence'] == 'manual_fixture']
        for f in fixtures:
            self.assertNotEqual(f['confidence'], 'real_structured')
    def test_preferred_primary_set(self):
        from smr_real_financial_source_registry import load_registry
        r = load_registry()
        self.assertIn('preferred_primary', r)

if __name__ == '__main__':
    unittest.main()
