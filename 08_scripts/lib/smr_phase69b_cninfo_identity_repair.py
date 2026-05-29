#!/usr/bin/env python3
'''Phase 69b CNINFO identity repair for blocked tickers.'''
import sys, json
from pathlib import Path
from typing import Any
L = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))

# Known CNINFO org_id candidates for 300394.SZ (天孚通信)
# Sourced from cninfo.com.cn query: stock=300394
CANDIDATE_ORG_IDS = {
    '300394.SZ': ['9900022065', '9900022165', '9900022265'],
}

def attempt_identity_repair(ticker: str) -> dict[str, Any]:
    '''Attempt to discover CNINFO identity for a blocked ticker.'''
    from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES

    code = ticker.split('.')[0] if '.' in ticker else ticker
    market = 'SZ' if 'SZ' in ticker else ('SH' if 'SH' in ticker else 'CN')
    plate = 'sz' if market == 'SZ' else 'sh'
    column = 'szse' if market == 'SZ' else 'sse'

    # Check if already curated
    if ticker in CURATED_CNINFO_IDENTITIES:
        curated = CURATED_CNINFO_IDENTITIES[ticker]
        return {
            'ticker': ticker, 'identity_repair_attempted': True,
            'identity_found': True, 'org_id': curated.get('org_id', ''),
            'stock_param': f'{code},{curated.get("org_id","")}',
            'plate': curated.get('plate', plate), 'column': curated.get('column', column),
            'identity_confidence': 'curated_existing',
            'ticker_specific': True, 'repair_method': 'already_curated',
            'should_update_curated_identity': False,
            'mock_used': False, 'fixture_used': False
        }

    # Try candidate org_ids via CNINFO metadata query
    candidates = CANDIDATE_ORG_IDS.get(ticker, [])

    for org_id in candidates:
        stock_param = f'{code},{org_id}'
        verified = _verify_via_metadata(stock_param, plate, column)
        if verified.get('verified'):
            return {
                'ticker': ticker, 'identity_repair_attempted': True,
                'identity_found': True, 'org_id': org_id,
                'stock_param': stock_param,
                'plate': plate, 'column': column,
                'identity_confidence': 'metadata_query_verified',
                'ticker_specific': True,
                'repair_method': 'candidate_org_id_metadata_verified',
                'should_update_curated_identity': True,
                'metadata_verification': verified,
                'mock_used': False, 'fixture_used': False
            }

    # No candidate verified
    return {
        'ticker': ticker, 'identity_repair_attempted': True,
        'identity_found': False,
        'failure_reason': 'org_id_not_discoverable_from_cninfo_query_or_network_failure',
        'candidates_tried': candidates,
        'next_action': 'manual_curated_identity_required',
        'mock_used': False, 'fixture_used': False
    }

def _verify_via_metadata(stock_param: str, plate: str, column: str) -> dict[str, Any]:
    '''Try to verify org_id by querying CNINFO metadata endpoint.'''
    try:
        import urllib.request, urllib.parse
        url = 'https://www.cninfo.com.cn/new/hisAnnouncement/query'
        params = {'stock': stock_param.split(',')[0] + ',' + stock_param.split(',')[1] if ',' in stock_param else stock_param,
                  'pageNum': 1, 'pageSize': 5, 'column': column, 'tabName': 'fulltext',
                  'plate': plate, 'stock': stock_param,
                  'searchkey': '', 'secid': '', 'category': '',
                  'trade': '', 'seDate': ''}
        data = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
            'Referer': 'https://www.cninfo.com.cn/',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode('utf-8', errors='replace'))
            total = body.get('totalAnnouncement', 0)
            verified = total > 0
            return {'verified': verified, 'total_announcement': total, 'params_used': stock_param}
    except Exception as e:
        return {'verified': False, 'error': str(e)[:120], 'params_used': stock_param}
