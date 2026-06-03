import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase144_ticker_checklist_builder import build_ticker_checklists

class TestChecklists(unittest.TestCase):
    def test_builds(self):
        r = build_ticker_checklists()
        self.assertEqual(r['phase144_ticker_checklists']['tickers'], 8)
        for c in r['phase144_ticker_checklists']['checklists']:
            self.assertGreaterEqual(len(c['items']), 5)

if __name__ == '__main__':
    unittest.main()
