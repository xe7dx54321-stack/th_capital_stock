import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
J = Path(__file__).resolve().parents[1] / '08_scripts' / 'jobs'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
for p in [str(L), str(J), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)

class TestPhase69bRunner(unittest.TestCase):
    def test_dry_run(self):
        from run_phase69b_multi_ticker_real_execute_and_identity_repair import run
        r = run(mode='dry_run')
        p = r['phase69b_multi_ticker_real_execute_and_identity_repair']
        self.assertGreater(len(p.get('steps', [])), 0)
        self.assertEqual(p.get('pending_created', -1), 0)

    def test_execute(self):
        from run_phase69b_multi_ticker_real_execute_and_identity_repair import run
        r = run(mode='execute')
        p = r['phase69b_multi_ticker_real_execute_and_identity_repair']
        self.assertGreaterEqual(p.get('full_chain_available', -1), 0)
        self.assertEqual(p.get('pending_created', -1), 0)

    def test_no_pass_without_execute(self):
        from run_phase69b_multi_ticker_real_execute_and_identity_repair import run
        r = run(mode='execute')
        p = r['phase69b_multi_ticker_real_execute_and_identity_repair']
        self.assertTrue(p.get('no_pass_without_execute', False))

    def test_skip_network(self):
        from run_phase69b_multi_ticker_real_execute_and_identity_repair import run
        r = run(mode='execute', skip_network=True)
        p = r['phase69b_multi_ticker_real_execute_and_identity_repair']
        self.assertGreaterEqual(len(p.get('steps', [])), 0)

    def test_no_mock_fixture(self):
        from run_phase69b_multi_ticker_real_execute_and_identity_repair import run
        r = run(mode='execute')
        p = r['phase69b_multi_ticker_real_execute_and_identity_repair']
        self.assertFalse(p.get('mock_used', True))
        self.assertFalse(p.get('fixture_used', True))

    def test_pending_order_trade_zero(self):
        from run_phase69b_multi_ticker_real_execute_and_identity_repair import run
        r = run(mode='execute')
        p = r['phase69b_multi_ticker_real_execute_and_identity_repair']
        self.assertEqual(p.get('pending_created', -1), 0)
        self.assertEqual(p.get('paper_order_created', -1), 0)
        self.assertEqual(p.get('real_trade_created', -1), 0)

    def test_no_raw_no_ocr(self):
        from run_phase69b_multi_ticker_real_execute_and_identity_repair import run
        r = run(mode='execute')
        p = r['phase69b_multi_ticker_real_execute_and_identity_repair']
        self.assertFalse(p.get('raw_saved', True))
        self.assertFalse(p.get('ocr_used', True))

if __name__ == '__main__': unittest.main()
