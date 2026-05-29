#!/usr/bin/env python3
'''Multi-ticker high-value disclosure selector.'''
import sys
from pathlib import Path
from typing import Any
L = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))

ADMIN_KEYWORDS = ['股权激励','限制性股票','股票期权','独立董事','监事会','董事会决议','法律意见书','律师事务所','公告编号','减持','质押','回购','公司章程','股东大会','更正公告','提示性公告','归属价格','归属']

def select_multi_ticker_high_value(max_pdfs_per_ticker: int = 10) -> dict[str, Any]:
    from smr_multi_ticker_universe import load_universe
    from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES

    universe = load_universe()
    tickers = [t['ticker'] for t in universe.get('tickers', [])]
    rows = []
    total_selected = 0

    for t in tickers:
        curated = CURATED_CNINFO_IDENTITIES.get(t, {})
        if not curated:
            rows.append({'ticker': t, 'selected_pdfs': 0, 'ir_records': 0, 'reports': 0, 'admin_legal_filtered': 0, 'failure_reason': 'identity_missing'})
            continue
        # Use Phase 67 pool loader for 300308 (baseline), generic for others
        try:
            from smr_phase67_high_value_pdf_pool_loader import load_high_value_pool
            pool = load_high_value_pool(t, max_pages=3, max_pdfs=max_pdfs_per_ticker)
            p = pool.get('phase67b_high_value_pdf_pool', pool)
            rows.append({'ticker': t, 'selected_pdfs': p.get('high_value_pdfs', 0), 'ir_records': p.get('source_type_breakdown', {}).get('investor_relations_record', 0), 'reports': sum(v for k, v in p.get('source_type_breakdown', {}).items() if 'report' in k.lower()), 'admin_legal_filtered': p.get('administrative_legal_excluded', 0), 'failure_reason': None})
            total_selected += p.get('high_value_pdfs', 0)
        except Exception as e:
            rows.append({'ticker': t, 'selected_pdfs': 0, 'ir_records': 0, 'reports': 0, 'admin_legal_filtered': 0, 'failure_reason': str(e)[:120]})

    return {'tickers_checked': len(tickers), 'selected_total': total_selected, 'rows': rows}
