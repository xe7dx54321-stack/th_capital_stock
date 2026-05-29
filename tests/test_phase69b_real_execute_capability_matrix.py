import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
for p in [str(L), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)

class TestCapabilityMatrix(unittest.TestCase):
    def test_matrix_has_three_tickers(self):
        from build_phase69b_real_execute_capability_matrix import build
        r = build()
        cm = r['phase69b_real_execute_capability_matrix']
        self.assertEqual(cm['tickers_checked'], 3)

    def test_no_pass_without_execute(self):
        from build_phase69b_real_execute_capability_matrix import build
        r = build()
        cm = r['phase69b_real_execute_capability_matrix']
        self.assertEqual(cm['conflict_status'], 'no_pass_without_execute')

    def test_full_chain_count(self):
        from build_phase69b_real_execute_capability_matrix import build
        r = build()
        cm = r['phase69b_real_execute_capability_matrix']
        self.assertGreaterEqual(cm['full_chain_available'], 1)

    def test_rows_have_basis(self):
        from build_phase69b_real_execute_capability_matrix import build
        r = build()
        cm = r['phase69b_real_execute_capability_matrix']
        for row in cm['rows']:
            self.assertIn('basis', row)

    def test_blocked_rows_have_blocker(self):
        from build_phase69b_real_execute_capability_matrix import build
        r = build()
        cm = r['phase69b_real_execute_capability_matrix']
        for row in cm['rows']:
            if row['overall'] == 'blocked':
                self.assertIn('blocker', row)

    def test_no_mock_fixture(self):
        from build_phase69b_real_execute_capability_matrix import build
        r = build()
        cm = r['phase69b_real_execute_capability_matrix']
        self.assertFalse(cm.get('mock_used', True))
        self.assertFalse(cm.get('fixture_used', True))

    def test_pending_order_trade_zero(self):
        from build_phase69b_real_execute_capability_matrix import build
        r = build()
        cm = r['phase69b_real_execute_capability_matrix']
        self.assertEqual(cm.get('pending_created', -1), 0)
        self.assertEqual(cm.get('paper_order_created', -1), 0)
        self.assertEqual(cm.get('real_trade_created', -1), 0)

if __name__ == '__main__': unittest.main()
