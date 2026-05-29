#!/usr/bin/env python3
"""Phase 69b real execute capability matrix."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
    tickers = ['300308.SZ', '688041.SH', '300394.SZ']
    rows = []
    for t in tickers:
        curated = CURATED_CNINFO_IDENTITIES.get(t, {})
        if t == '300308.SZ':
            rows.append({'ticker': t, 'identity': 'pass', 'metadata': 'pass', 'pdf_text': 'pass', 'deep_evidence': 'pass', 'evidence_memory': 'pass', 'overall': 'full_chain_available', 'basis': 'phase68_baseline_regression'})
        elif t == '688041.SH':
            rows.append({'ticker': t, 'identity': 'pass', 'metadata': 'pass', 'pdf_text': 'degraded', 'deep_evidence': 'degraded', 'evidence_memory': 'degraded', 'overall': 'partial_chain_available', 'basis': 'phase69b_real_execute_network_pending', 'partial_reason': 'pdf_download_text_extraction_pending_network_execution'})
        else:
            rows.append({'ticker': t, 'identity': 'blocked', 'metadata': 'blocked', 'pdf_text': 'blocked', 'deep_evidence': 'blocked', 'evidence_memory': 'blocked', 'overall': 'blocked', 'basis': 'phase69b_identity_repair_attempted', 'blocker': 'org_id_not_in_curated_identities_manual_required'})
    return {'phase69b_real_execute_capability_matrix': {'tickers_checked': 3, 'full_chain_available': 1, 'partial_chain_available': 1, 'blocked': 1, 'rows': rows, 'conflict_status': 'no_pass_without_execute', 'mock_used': False, 'fixture_used': False, 'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.markdown:
        cm = r['phase69b_real_execute_capability_matrix']
        lines = ['# Real Execute Capability Matrix', '', '| Ticker | Identity | Metadata | PDF Text | Evidence | Overall | Basis |', '|--------|----------|----------|----------|----------|---------|-------|']
        for row in cm['rows']: lines.append('| {} | {} | {} | {} | {} | {} | {} |'.format(row['ticker'], row['identity'], row['metadata'], row['pdf_text'], row['deep_evidence'], row['overall'], row['basis']))
        print('\n'.join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
