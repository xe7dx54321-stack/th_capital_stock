#!/usr/bin/env python3
'''Multi-ticker disclosure identity resolver.'''
import sys
from pathlib import Path
from typing import Any
L = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES, _market_for_ticker

def resolve_multi_ticker_identities() -> dict[str, Any]:
    from smr_multi_ticker_universe import load_universe
    universe = load_universe()
    tickers = [t['ticker'] for t in universe.get('tickers', [])]
    rows = []
    resolved = 0
    missing = 0
    for t in tickers:
        curated = CURATED_CNINFO_IDENTITIES.get(t, {})
        market = _market_for_ticker(t)
        code = t.split('.')[0] if '.' in t else t
        if curated:
            resolved += 1
            rows.append({
                'ticker': t, 'identity_found': True,
                'stock_param': f'{code},{curated.get("org_id","")}',
                'org_id': curated.get('org_id', ''),
                'market': market,
                'plate': curated.get('plate', market.lower()),
                'column': curated.get('column', market.lower() + 'se'),
                'identity_confidence': 'verified' if curated.get('confidence', 0) >= 0.9 else 'discovered',
                'identity_source': curated.get('identity_source', 'curated')
            })
        else:
            missing += 1
            rows.append({
                'ticker': t, 'identity_found': False,
                'market': market,
                'failure_reason': 'org_id_missing_or_unverified_in_curated_identities',
                'action_required': 'add_curated_identity_or_run_cninfo_resolver'
            })
    return {
        'tickers_checked': len(tickers),
        'identity_resolved': resolved,
        'identity_missing': missing,
        'rows': rows,
        'mock_used': False,
        'fixture_used': False
    }
