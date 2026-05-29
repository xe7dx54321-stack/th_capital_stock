#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
sys.path.insert(0, str(R))
from build_phase62_real_chinese_business_text_dashboard import build

class TestDashboard(unittest.TestCase):
    def test_returns_valid(self):
        r = build(None, '300308.SZ')
        d = r['summary']
        self.assertFalse(d['phase50_fixture_used'])
        self.assertFalse(d['mock_text_used'])
        self.assertFalse(d['raw_content_saved'])
        self.assertFalse(d['ocr_used'])
        self.assertEqual(d['pending_created'], 0)
        self.assertEqual(d['guard_status'], 'pass')
if __name__=='__main__': unittest.main()
