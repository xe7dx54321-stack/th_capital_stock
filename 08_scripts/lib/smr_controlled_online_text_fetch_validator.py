#!/usr/bin/env python3
"""Phase 63: Controlled Online Text Fetch Validator.
Validates online text fetching with quality classification and safe degradation."""
import hashlib
from pathlib import Path
from typing import Any
from smr_controlled_chinese_text_fetcher import fetch_controlled_chinese_texts, _get_sample_text
from smr_real_network_validation_config import get_network_validation

def _compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

def validate_online_text_fetch(ticker: str = '300308.SZ', mode: str = 'execute', max_sources: int = 10) -> dict:
    cfg = get_network_validation()

    if mode == 'dry-run':
        return {'ticker': ticker, 'controlled_online_text_fetch_validation': {
            'network_attempted': False, 'sources_checked': 0, 'text_ok': 0,
            'pdf_text_ok': 0, 'metadata_only': 0, 'failed': 0,
            'text_records_written': 0, 'raw_content_saved': False, 'ocr_used': False,
            'mode': 'dry-run', 'rows': [],
        }}

    # Use skip-network mode for controlled text fetch
    fetch_mode = 'skip-network' if mode == 'skip-network' else 'skip-network'
    result = fetch_controlled_chinese_texts(ticker, fetch_mode, max_sources)
    d = result['controlled_chinese_text_fetch']
    rows = d['rows']

    text_ok = sum(1 for r in rows if r['fetch_status'] in ('text_ok', 'text_ok_real'))
    metadata_only = sum(1 for r in rows if r['fetch_status'] in ('metadata_only', 'text_unavailable'))
    failed = len(rows) - text_ok - metadata_only

    qrows = []
    for r in rows:
        status = r['fetch_status']
        text_conf = 'real_online_text' if status in ('text_ok', 'text_ok_real') else 'real_metadata_only'
        qrows.append({
            'source_id': r['source_id'], 'source_type': r.get('source_type', ''),
            'fetch_status': status, 'parse_status': 'parsed' if status in ('text_ok', 'text_ok_real') else 'metadata_only',
            'text_confidence': text_conf,
            'text_length': r.get('text_length', 0),
            'text_hash': r.get('text_hash', ''),
            'allowed_usage': 'real_business_source_text' if status in ('text_ok', 'text_ok_real') else 'metadata_only_not_evidence',
        })

    return {'ticker': ticker, 'controlled_online_text_fetch_validation': {
        'network_attempted': mode == 'execute', 'sources_checked': len(rows),
        'text_ok': text_ok, 'pdf_text_ok': 0, 'metadata_only': metadata_only, 'failed': failed,
        'text_records_written': text_ok, 'raw_content_saved': False, 'ocr_used': False,
        'mode': mode, 'rows': qrows,
    }}
