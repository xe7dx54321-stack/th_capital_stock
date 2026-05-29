import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
for p in [str(L), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)

class TestGenericVsTickerSpecific(unittest.TestCase):
    def test_report_outputs(self):
        from build_phase69b_generic_vs_ticker_specific_report import build
        r = build()
        rep = r.get('generic_vs_ticker_specific_report', r)
        self.assertIsNotNone(rep)

    def test_has_generic_capabilities(self):
        from build_phase69b_generic_vs_ticker_specific_report import build
        r = build()
        rep = r.get('generic_vs_ticker_specific_report', r)
        self.assertIn('generic_capabilities', rep)
        self.assertGreater(len(rep['generic_capabilities']), 0)

    def test_has_ticker_specific_requirements(self):
        from build_phase69b_generic_vs_ticker_specific_report import build
        r = build()
        rep = r.get('generic_vs_ticker_specific_report', r)
        self.assertIn('ticker_specific_requirements', rep)

    def test_has_not_generalized(self):
        from build_phase69b_generic_vs_ticker_specific_report import build
        r = build()
        rep = r.get('generic_vs_ticker_specific_report', r)
        self.assertIn('not_yet_generalized', rep)

    def test_does_not_overclaim(self):
        from build_phase69b_generic_vs_ticker_specific_report import build
        r = build()
        rep = r.get('generic_vs_ticker_specific_report', r)
        text = str(rep).lower()
        self.assertNotIn('fully generalized for all', text)

if __name__ == '__main__': unittest.main()
