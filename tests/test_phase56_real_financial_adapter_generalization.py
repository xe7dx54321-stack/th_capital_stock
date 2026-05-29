import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class Phase56GenTests(unittest.TestCase):
    def test_generic_caps_listed(self):
        from smr_real_financial_source_registry import load_registry
        r = load_registry()
        self.assertIn('sources', r)
    def test_not_claiming_global(self):
        import json
        from smr_real_financial_source_registry import load_registry
        r = json.dumps(load_registry(), ensure_ascii=False)
        self.assertNotIn('automatically generalizes', r)

if __name__ == '__main__':
    unittest.main()
