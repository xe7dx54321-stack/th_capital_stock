#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
sys.path.insert(0, str(R))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'))
from build_phase62_real_chinese_business_evidence_rerun import build

class TestRerun(unittest.TestCase):
    def test_returns_valid(self):
        r = build(None, '300308.SZ')
        d = r['real_chinese_business_evidence_rerun']
        self.assertGreater(d['real_chinese_chunks_scanned'], 0)
        self.assertFalse(d['mock_text_used'])
        self.assertEqual(d['guard_status'], 'pass')

class TestDashboard(unittest.TestCase):
    def test_dashboard_valid(self):
        r = build(None, '300308.SZ')
        d = r['real_chinese_business_evidence_rerun']
        self.assertFalse(d['fixture_text_used_for_research'])
if __name__=='__main__': unittest.main()
