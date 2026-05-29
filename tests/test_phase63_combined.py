#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_controlled_online_text_fetch_validator import validate_online_text_fetch
from smr_controlled_pdf_text_extractor import run_pdf_text_extraction
from smr_real_text_extraction_quality_classifier import classify_extraction_quality

class TestFetch(unittest.TestCase):
    def test_skip_network(self):
        r = validate_online_text_fetch('300308.SZ', 'skip-network')
        self.assertGreater(r['controlled_online_text_fetch_validation']['text_ok'], 0)
        self.assertFalse(r['controlled_online_text_fetch_validation']['ocr_used'])
    def test_quality_classification(self):
        r = classify_extraction_quality('300308.SZ')
        q = r['real_text_extraction_quality']
        self.assertGreater(q['metadata_only_not_evidence'], 0)

class TestPDF(unittest.TestCase):
    def test_no_ocr(self):
        r = run_pdf_text_extraction('300308.SZ')
        self.assertFalse(r['pdf_text_extraction_report']['ocr_used'])
    def test_no_raw_pdf(self):
        r = run_pdf_text_extraction('300308.SZ')
        self.assertFalse(r['pdf_text_extraction_report']['raw_pdf_saved'])
    def test_failed_has_reason(self):
        r = run_pdf_text_extraction('300308.SZ')
        for row in r['pdf_text_extraction_report']['rows']:
            if row['extraction_status'] == 'pdf_text_failed':
                self.assertIsNotNone(row['failure_reason'])

class TestQuality(unittest.TestCase):
    def test_metadata_not_evidence(self):
        r = classify_extraction_quality('300308.SZ')
        for row in r['real_text_extraction_quality']['rows']:
            if row['quality_status'] == 'metadata_only_not_evidence':
                self.assertEqual(row['allowed_usage'], 'metadata_only_not_evidence')
if __name__=='__main__': unittest.main()
