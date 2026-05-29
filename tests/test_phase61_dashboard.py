#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'))
from build_phase61_real_business_evidence_dashboard import build_dashboard

class TestPhase61Dashboard(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = build_dashboard('300308.SZ')
        d = r['summary']
        self.assertEqual(d['ticker'], '300308.SZ')
        self.assertEqual(d['industry'], 'ai_optical_module')
        self.assertEqual(d['business_variables_defined'], 7)

    def test_no_pending_order_trade(self):
        r = build_dashboard('300308.SZ')
        d = r['summary']
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['paper_order_created'], 0)
        self.assertEqual(d['real_trade_created'], 0)

    def test_real_not_mock(self):
        r = build_dashboard('300308.SZ')
        d = r['summary']
        self.assertTrue(d['real_business_evidence_used'])
        self.assertFalse(d['mock_business_evidence_used'])

    def test_guard_pass(self):
        r = build_dashboard('300308.SZ')
        d = r['summary']
        self.assertEqual(d['guard_status'], 'pass')

    def test_real_text_sources(self):
        r = build_dashboard('300308.SZ')
        d = r['summary']
        self.assertGreater(d['real_text_sources_available'], 0)

if __name__ == '__main__': unittest.main()
