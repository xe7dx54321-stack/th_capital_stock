#!/usr/bin/env python3
import unittest, sys
sys.path.insert(0, '08_scripts/lib')
sys.path.insert(0, '08_scripts/reporting')
from build_phase58_industry_aware_financial_brief_section import build


class TestBriefSection(unittest.TestCase):
    def test_has_all_sections(self):
        r = build(None, '300308.SZ')
        d = r['industry_aware_financial_brief_section']
        self.assertIsInstance(d['what_we_see'], list)
        self.assertIsInstance(d['what_it_means'], list)
        self.assertIsInstance(d['what_we_cannot_conclude'], list)

    def test_no_teaching_style(self):
        r = build(None, '300308.SZ')
        text = str(r)
        self.assertNotIn('下一步', text)
        self.assertNotIn('建议关注', text)

    def test_cannot_conclude_present(self):
        r = build(None, '300308.SZ')
        d = r['industry_aware_financial_brief_section']
        cannot_text = ' '.join(d['what_we_cannot_conclude'])
        self.assertIn('800G', cannot_text or '')
        self.assertIn('ASP', cannot_text or '')


if __name__ == '__main__':
    unittest.main()
