#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_chinese_text_normalizer import normalize_chinese_texts, _detect_qa_structure, _remove_disclaimers

class TestTextNormalizer(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = normalize_chinese_texts('300308.SZ')
        d = r['chinese_text_normalization']
        self.assertGreater(d['texts_checked'], 0)
    def test_qa_detected(self):
        r = normalize_chinese_texts('300308.SZ')
        d = r['chinese_text_normalization']
        self.assertGreater(d['qa_structure_detected'], 0)
    def test_short_text_filtered(self):
        r = normalize_chinese_texts('300308.SZ')
        for row in r['chinese_text_normalization']['rows']:
            self.assertIn('status', row)
    def test_qa_detection(self):
        self.assertTrue(_detect_qa_structure('问题一：测试？\n答：回复内容。'))
        self.assertFalse(_detect_qa_structure('普通文本无问答结构。'))
    def test_disclaimer_removal(self):
        text, count = _remove_disclaimers('本公司及董事会全体成员保证信息披露的内容真实。正文开始。')
        self.assertGreater(count, 0)
        self.assertIn('正文开始', text)
if __name__=='__main__': unittest.main()
