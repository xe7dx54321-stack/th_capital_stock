#!/usr/bin/env python3
"""Phase 63: CNINFO Real Network Fetch Validator.
Validates CNINFO metadata fetch over real network, with safe degradation."""
import json, time, hashlib
from pathlib import Path
from typing import Any
from smr_real_network_validation_config import get_network_validation
from smr_cninfo_business_metadata_connector import fetch_cninfo_metadata, CNINFO_API, _classify_cninfo_type

def _try_real_cninfo_request(ticker: str) -> tuple[bool, list[dict], str]:
    """Try real CNINFO API call. Returns (success, rows, error_msg)."""
    cfg = get_network_validation()
    timeout = cfg.get('default_timeout_seconds', 20)
    try:
        import urllib.request, urllib.parse
        stock_code = ticker.split('.')[0]
        results = []
        for page in range(1, 3):
            data = urllib.parse.urlencode({
                'pageNum': page, 'pageSize': 30,
                'column': 'szse', 'tabName': 'fulltext',
                'plate': 'sz', 'stock': stock_code,
                'searchkey': '', 'secid': '',
                'category': '', 'trade': '', 'seDate': '',
            }).encode('utf-8')
            req = urllib.request.Request(CNINFO_API, data=data, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode('utf-8'))
                anns = body.get('announcements', []) or body.get('classifiedAnnouncements', [])
                if not anns and isinstance(body, list):
                    anns = body
                for ann in anns:
                    if isinstance(ann, dict):
                        results.append({
                            'title': ann.get('announcementTitle', ''),
                            'source_type': _classify_cninfo_type(ann.get('announcementTitle', '')),
                            'publish_date': str(ann.get('announcementTime', '')[:10]),
                            'adjunctUrl': ann.get('adjunctUrl', ''),
                        })
            time.sleep(0.8)
        return (True, results, '')
    except Exception as e:
        return (False, [], str(e)[:120])

def validate_cninfo_network(ticker: str = '300308.SZ', mode: str = 'execute') -> dict:
    cfg = get_network_validation()
    if mode == 'dry-run':
        return {'ticker': ticker, 'cninfo_real_network_validation': {
            'mode': 'dry-run', 'network_attempted': False, 'network_available': False,
            'sources_requested': 0, 'metadata_sources_found': 0,
            'raw_content_saved': False, 'ocr_used': False, 'status': 'dry_run_no_network',
            'note': 'Dry-run mode. No network calls.', 'rows': [], 'failure_rows': [],
        }}
    if mode == 'skip-network':
        result = fetch_cninfo_metadata(ticker, 'skip-network')
        d = result['cninfo_metadata_inventory']
        return {'ticker': ticker, 'cninfo_real_network_validation': {
            'mode': 'skip-network', 'network_attempted': False, 'network_available': False,
            'sources_requested': 0, 'metadata_sources_found': d['sources_found'],
            'raw_content_saved': False, 'ocr_used': False, 'status': 'skip_network',
            'note': 'Skip-network mode. Using known metadata catalog.',
            'source_types': d['source_types'], 'rows': d['rows'][:15], 'failure_rows': [],
        }}

    # execute mode
    success, results, error = _try_real_cninfo_request(ticker)
    if not success:
        return {'ticker': ticker, 'cninfo_real_network_validation': {
            'mode': 'execute', 'network_attempted': True, 'network_available': False,
            'metadata_sources_found': 0, 'status': 'degraded_network_unavailable',
            'fallback_used': cfg.get('allow_mock_fallback', False),
            'mock_used': False, 'fixture_used': False,
            'error_reason': error, 'raw_content_saved': False, 'ocr_used': False,
            'rows': [], 'failure_rows': [],
        }}

    type_counts: dict[str, int] = {}
    rows = []
    for i, r in enumerate(results):
        st = r['source_type']
        type_counts[st] = type_counts.get(st, 0) + 1
        rows.append({
            'source_id': f'cninfo_real_{ticker.split(".")[0]}_{st}_{i+1:03d}',
            'title': r['title'][:60], 'source_type': st,
            'publish_date': r['publish_date'], 'fetch_status': 'metadata_ok',
        })

    return {'ticker': ticker, 'cninfo_real_network_validation': {
        'mode': 'execute', 'network_attempted': True, 'network_available': True,
        'sources_requested': 20, 'metadata_sources_found': len(results),
        'metadata_sources_valid': len(results), 'source_types': type_counts,
        'raw_content_saved': False, 'ocr_used': False, 'status': 'network_ok',
        'rows': rows, 'failure_rows': [],
    }}
