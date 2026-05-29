#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_real_quoted_span_validator import validate_quoted_spans, _is_title_only, _is_boilerplate, _is_marketing_slogan_only

class TestRealQuotedSpanValidator(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = validate_quoted_spans('300308.SZ')
        self.assertIn('real_quoted_span_validation', r)
        d = r['real_quoted_span_validation']
        self.assertGreater(d['spans_checked'], 0)

    def test_all_spans_passed(self):
        r = validate_quoted_spans('300308.SZ')
        d = r['real_quoted_span_validation']
        self.assertEqual(d['spans_rejected'], 0)
        self.assertGreater(d['spans_passed'], 0)

    def test_title_only_detection(self):
        self.assertTrue(_is_title_only('公告：关于XXXX'))
        self.assertFalse(_is_title_only('公司800G产品已批量交付，下游需求旺盛。'))

    def test_boilerplate_detection(self):
        self.assertTrue(_is_boilerplate('风险提示：投资有风险'))
        self.assertFalse(_is_boilerplate('公司800G产品出货节奏良好。'))

    def test_marketing_slogan_detection(self):
        self.assertTrue(_is_marketing_slogan_only('行业领先'))
        self.assertFalse(_is_marketing_slogan_only('公司在OFC 2025展示了1.6T产品并已向客户送样。'))

    def test_mismatched_span_rejected(self):
        # A span that cannot exist in source text should be rejected
        r = validate_quoted_spans('300308.SZ')
        for row in r['real_quoted_span_validation']['rows']:
            self.assertNotEqual(row['validation_status'], 'rejected')

if __name__ == '__main__': unittest.main()
