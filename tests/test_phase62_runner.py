#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
sys.path.insert(0, str(R))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'jobs'))
from build_phase62_real_chinese_business_text_dashboard import build
from run_phase62_real_chinese_business_text_pipeline import run_loop

class TestDashboard(unittest.TestCase):
    def test_returns_valid(self):
        r = build(None, '300308.SZ')
        d = r['summary']
        self.assertFalse(d['phase50_fixture_used'])
        self.assertFalse(d['mock_text_used'])
        self.assertFalse(d['raw_content_saved'])
        self.assertEqual(d['pending_created'], 0)

class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        r = run_loop('300308.SZ', 'dry-run')
        d = r['phase62_real_chinese_business_text_pipeline']
        self.assertFalse(d['phase50_fixture_used'])
    def test_execute(self):
        r = run_loop('300308.SZ', 'execute')
        d = r['phase62_real_chinese_business_text_pipeline']
        self.assertEqual(len(d['steps']), 9)
        self.assertFalse(d['mock_text_used'])
        self.assertEqual(d['pending_created'], 0)
if __name__=='__main__': unittest.main()
