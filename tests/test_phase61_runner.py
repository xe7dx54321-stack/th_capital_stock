#!/usr/bin/env python3
import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'jobs'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'))
from run_phase61_real_business_evidence_pipeline import run_loop

class TestPhase61Runner(unittest.TestCase):
    def test_dry_run_works(self):
        r = run_loop('300308.SZ', 'dry-run')
        d = r['phase61_real_business_evidence_pipeline']
        self.assertIn('steps', d)
        self.assertEqual(len(d['steps']), 11)
        self.assertFalse(d['mock_business_evidence_used'])

    def test_execute_works(self):
        r = run_loop('300308.SZ', 'execute')
        d = r['phase61_real_business_evidence_pipeline']
        for step in d['steps']:
            self.assertEqual(step['status'], 'ok')

    def test_no_pending_order_trade(self):
        r = run_loop('300308.SZ', 'execute')
        d = r['phase61_real_business_evidence_pipeline']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)

    def test_real_business_used(self):
        r = run_loop('300308.SZ', 'execute')
        d = r['phase61_real_business_evidence_pipeline']
        self.assertTrue(d['real_business_evidence_used'])
        self.assertFalse(d['mock_business_evidence_used'])

if __name__ == '__main__': unittest.main()
