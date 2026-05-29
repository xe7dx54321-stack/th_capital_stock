#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
J = Path(__file__).resolve().parents[1] / '08_scripts' / 'jobs'
sys.path.insert(0, str(R)); sys.path.insert(0, str(J))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'))
from build_phase63_real_network_business_evidence_rerun import build
from build_phase63_real_network_business_evidence_brief import build as brief_build
from build_phase63_real_network_source_validation_dashboard import build as dash_build
from run_phase63_real_network_source_validation import run_loop

class TestRerun(unittest.TestCase):
    def test_no_fixture(self):
        r = build(None, '300308.SZ')
        self.assertFalse(r['real_network_business_evidence_rerun']['phase50_fixture_used'])
    def test_no_mock(self):
        r = build(None, '300308.SZ')
        self.assertFalse(r['real_network_business_evidence_rerun']['mock_text_used'])
    def test_pending_zero(self):
        r = build(None, '300308.SZ')
        self.assertEqual(r['real_network_business_evidence_rerun']['pending_created'], 0)

class TestBrief(unittest.TestCase):
    def test_no_forbidden(self):
        r = brief_build(None, '300308.SZ')
        d = r['real_network_business_evidence_brief']
        self.assertFalse(d['phase50_fixture_used'])
        self.assertEqual(d['pending_created'], 0)

class TestDashboard(unittest.TestCase):
    def test_valid(self):
        r = dash_build(None, '300308.SZ')
        d = r['summary']
        self.assertFalse(d['phase50_fixture_used'])
        self.assertFalse(d['mock_text_used'])
        self.assertFalse(d['raw_content_saved'])
        self.assertEqual(d['pending_created'], 0)

class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        r = run_loop('300308.SZ', 'dry-run')
        d = r['phase63_real_network_source_validation']
        self.assertFalse(d['phase50_fixture_used'])
        self.assertEqual(len(d['steps']), 8)
    def test_execute(self):
        r = run_loop('300308.SZ', 'execute')
        d = r['phase63_real_network_source_validation']
        self.assertFalse(d['mock_text_used'])
        self.assertEqual(d['pending_created'], 0)
if __name__=='__main__': unittest.main()
