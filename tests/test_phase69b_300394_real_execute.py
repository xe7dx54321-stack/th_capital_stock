import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
J = Path(__file__).resolve().parents[1] / '08_scripts' / 'jobs'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
for p in [str(L), str(J), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)

class Test300394RealExecute(unittest.TestCase):
    def test_dry_run_outputs_identity_status(self):
        from run_phase69b_300394_real_execute import run
        r = run(mode='dry_run')
        ex = r['phase69b_300394_real_execute']
        self.assertIn('identity_repaired', ex)

    def test_blocked_if_identity_missing(self):
        from run_phase69b_300394_real_execute import run
        r = run(mode='execute')
        ex = r['phase69b_300394_real_execute']
        if not ex.get('identity_repaired'):
            self.assertIn('blocker', ex)
            self.assertEqual(ex.get('overall_status'), 'blocked')

    def test_blocked_has_blocker_detail(self):
        from run_phase69b_300394_real_execute import run
        r = run(mode='execute')
        ex = r['phase69b_300394_real_execute']
        if ex.get('overall_status') == 'blocked':
            self.assertIn('blocker', ex)
            self.assertTrue(len(ex.get('blocker', '')) > 0)

    def test_no_mock_fixture(self):
        from run_phase69b_300394_real_execute import run
        r = run(mode='execute')
        ex = r['phase69b_300394_real_execute']
        self.assertFalse(ex.get('mock_used', True))
        self.assertFalse(ex.get('fixture_used', True))

    def test_pending_order_trade_zero(self):
        from run_phase69b_300394_real_execute import run
        r = run(mode='execute')
        ex = r['phase69b_300394_real_execute']
        self.assertEqual(ex.get('pending_created', -1), 0)
        self.assertEqual(ex.get('paper_order_created', -1), 0)
        self.assertEqual(ex.get('real_trade_created', -1), 0)

    def test_no_raw_no_ocr(self):
        from run_phase69b_300394_real_execute import run
        r = run(mode='execute')
        ex = r['phase69b_300394_real_execute']
        self.assertFalse(ex.get('raw_saved', True))
        self.assertFalse(ex.get('ocr_used', True))

    def test_report_outputs(self):
        from build_phase69b_300394_real_execute_report import build
        r = build()
        self.assertIsNotNone(r)
        self.assertIn('300394', str(r))

if __name__ == '__main__': unittest.main()
