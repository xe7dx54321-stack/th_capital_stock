#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_chinese_business_source_registry import load_registry, get_sources, build_registry_report

class TestRegistry(unittest.TestCase):
    def test_loads(self):
        r = build_registry_report()
        self.assertGreater(r['sources_count'], 0)
        self.assertFalse(r['raw_content_saved'])
        self.assertFalse(r['ocr_allowed'])
    def test_sources_raw_false(self):
        for s in get_sources():
            self.assertFalse(s['raw_content_saved'])
            self.assertFalse(s['ocr_allowed'])
    def test_priorities(self):
        sources = get_sources()
        priorities = {s['priority'] for s in sources}
        self.assertIn('P0', priorities)
    def test_allowed_usage(self):
        for s in get_sources():
            self.assertIn('allowed_usage', s)
            self.assertNotEqual(s['allowed_usage'], '')
if __name__=='__main__': unittest.main()
