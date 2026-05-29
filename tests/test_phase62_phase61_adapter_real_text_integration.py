#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
L = R.parents[0] / '08_scripts' / 'lib'
sys.path.insert(0, str(L)); sys.path.insert(0, str(R))
from build_phase62_phase61_adapter_real_text_integration import build

class TestAdapterIntegration(unittest.TestCase):
    def test_returns_valid(self):
        r = build(None, '300308.SZ')
        d = r['phase61_adapter_real_text_integration']
        self.assertFalse(d['mock_sources_used_for_research'])
        self.assertFalse(d['raw_content_saved'])
        self.assertFalse(d['ocr_used'])
    def test_fixture_not_used(self):
        r = build(None, '300308.SZ')
        d = r['phase61_adapter_real_text_integration']
        self.assertFalse(d['fixture_text_used_for_research'])
if __name__=='__main__': unittest.main()
