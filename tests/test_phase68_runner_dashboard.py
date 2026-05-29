import unittest, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / '08_scripts' / 'jobs'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
if str(J) not in sys.path: sys.path.insert(0, str(J))
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        from run_phase68_evidence_memory_and_brief import run
        r = run('300308.SZ', dry_run=True, mode='dry_run')
        p = r['phase68_evidence_memory_and_brief']
        self.assertGreater(len(p['steps']), 0)
        self.assertEqual(p['mock_used'], False)
        self.assertEqual(p['fixture_used'], False)
        self.assertEqual(p['pending_created'], 0)
        self.assertEqual(p['paper_order_created'], 0)
        self.assertEqual(p['real_trade_created'], 0)

    def test_execute(self):
        from run_phase68_evidence_memory_and_brief import run
        r = run('300308.SZ', dry_run=False, mode='execute')
        p = r['phase68_evidence_memory_and_brief']
        self.assertGreater(p['evidence_memory_records'], 0)
        self.assertGreater(p['claims_supported'], 0)
        self.assertEqual(p['brief_quality_status'], 'pass')

    def test_skip_write(self):
        from run_phase68_evidence_memory_and_brief import run
        r = run('300308.SZ', skip_write=True, mode='execute')
        p = r['phase68_evidence_memory_and_brief']
        self.assertEqual(p['brief_quality_status'], 'pass')

class TestDashboard(unittest.TestCase):
    def test_dashboard(self):
        from build_phase68_evidence_memory_brief_dashboard import build
        r = build()
        s = r['summary']
        self.assertGreater(s['evidence_memory_records'], 0)
        self.assertEqual(s['brief_quality_status'], 'pass')
        self.assertEqual(s['system_terms_found'], 0)
        self.assertEqual(s['overclaim_violations'], 0)
        self.assertEqual(s['pending_created'], 0)
        self.assertEqual(s['paper_order_created'], 0)
        self.assertEqual(s['real_trade_created'], 0)
        self.assertEqual(s['mock_used'], False)

if __name__ == '__main__': unittest.main()
