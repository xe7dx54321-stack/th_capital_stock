#!/usr/bin/env python3
from __future__ import annotations

def fetch_cninfo_financial_report_text(ticker='300308.SZ', mode='dry-run'):
    is_dry = mode == 'dry-run'
    skip_network = mode == 'skip-network'
    metadata_only = mode == 'metadata-only'
    
    return {'ticker': ticker, 'cninfo_financial_report_text_fetch': {
        'mode': mode,
        'reports_checked': 0,
        'financial_text_available': 0,
        'metadata_only': 0,
        'raw_content_saved': False,
        'ocr_used': False,
        'extractable_metric_candidates': [],
        'records_written': 0,
        'confidence': 'real_report_text_extracted_or_metadata_only',
        'note': 'CNINFO text fallback interface. First version does not download raw reports. No OCR. Text extraction from reports is a future capability.',
        'reason': 'cninfo_network_fetch_required_for_real_text' if not skip_network and not is_dry else 'dry_run_no_fetch'
    }}
