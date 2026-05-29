import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
for p in [str(L), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)

class TestPhase69bDashboard(unittest.TestCase):
    def test_dashboard_outputs(self):
        from build_phase69b_real_execute_dashboard import build
        r = build()
        s = r['summary']
        self.assertEqual(s.get('tickers_checked', 0), 3)

    def test_no_pass_without_execute(self):
        from build_phase69b_real_execute_dashboard import build
        r = build()
        s = r['summary']
        self.assertTrue(s.get('no_pass_without_execute', False))

    def test_pending_order_trade_zero(self):
        from build_phase69b_real_execute_dashboard import build
        r = build()
        s = r['summary']
        self.assertEqual(s.get('pending_created', -1), 0)
        self.assertEqual(s.get('paper_order_created', -1), 0)
        self.assertEqual(s.get('real_trade_created', -1), 0)

    def test_no_mock_fixture(self):
        from build_phase69b_real_execute_dashboard import build
        r = build()
        s = r['summary']
        self.assertFalse(s.get('mock_used', True))
        self.assertFalse(s.get('fixture_used', True))

    def test_no_raw_no_ocr(self):
        from build_phase69b_real_execute_dashboard import build
        r = build()
        s = r['summary']
        self.assertFalse(s.get('raw_saved', True))
        self.assertFalse(s.get('ocr_used', True))

    def test_brief_quality_status(self):
        from build_phase69b_real_execute_dashboard import build
        r = build()
        s = r['summary']
        self.assertEqual(s.get('brief_quality_status', ''), 'pass')

    def test_has_capability_counts(self):
        from build_phase69b_real_execute_dashboard import build
        r = build()
        s = r['summary']
        self.assertIn('full_chain_available', s)
        self.assertIn('partial_chain_available', s)
        self.assertIn('blocked', s)

if __name__ == '__main__': unittest.main()
