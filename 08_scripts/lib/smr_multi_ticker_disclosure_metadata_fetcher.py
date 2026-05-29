#!/usr/bin/env python3
'''Multi-ticker disclosure metadata fetcher.'''
import sys, json
from pathlib import Path
from typing import Any
L = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))

def fetch_multi_ticker_metadata(dry_run: bool = False, max_pages: int = 3, page_size: int = 30) -> dict[str, Any]:
    from smr_multi_ticker_universe import load_universe
    from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
    from smr_cninfo_pagination_query_engine import pagination_query

    universe = load_universe()
    tickers = [t['ticker'] for t in universe.get('tickers', [])]
    rows = []
    success = 0
    failed = 0

    for t in tickers:
        curated = CURATED_CNINFO_IDENTITIES.get(t, {})
        if dry_run:
            rows.append({'ticker': t, 'metadata_sources_found': 0, 'pdf_urls_found': 0, 'status': 'dry_run', 'failure_reason': None})
            continue
        if not curated:
            failed += 1
            rows.append({'ticker': t, 'metadata_sources_found': 0, 'pdf_urls_found': 0, 'status': 'metadata_unavailable', 'failure_reason': 'identity_missing'})
            continue
        try:
            code = t.split('.')[0]
            stock_param = f'{code},{curated.get("org_id","")}'
            result = pagination_query(stock_param=stock_param, plate=curated.get('plate','sz'), column=curated.get('column','szse'), max_pages=max_pages, page_size=page_size)
            m = result.get('cninfo_pagination_inventory', result)
            found = m.get('metadata_rows_after_dedupe', m.get('metadata_rows_collected', 0))
            pdf_count = sum(1 for r in m.get('rows', []) if r.get('adjunct_url'))
            success += 1
            rows.append({'ticker': t, 'metadata_sources_found': found, 'pdf_urls_found': pdf_count, 'status': 'metadata_available', 'failure_reason': None})
        except Exception as e:
            failed += 1
            rows.append({'ticker': t, 'metadata_sources_found': 0, 'pdf_urls_found': 0, 'status': 'metadata_fetch_failed', 'failure_reason': str(e)[:120]})

    return {'tickers_checked': len(tickers), 'metadata_success': success, 'metadata_failed': failed, 'rows': rows, 'mock_used': False, 'fixture_used': False}
