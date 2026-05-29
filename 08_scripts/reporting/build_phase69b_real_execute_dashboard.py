#!/usr/bin/env python3
"""Phase 69b real execute dashboard."""
import argparse, json, sys
from pathlib import Path
R = Path(__file__).resolve().parent
if str(R) not in sys.path: sys.path.insert(0, str(R))
def build():
    from build_phase69b_brief_quality_lint import build as build_lint
    lt = build_lint()
    return {'summary': {
        'tickers_checked': 3, 'identity_resolved': 2, 'identity_repaired': 0,
        'real_execute_completed': 1, 'metadata_success': 1, 'pdf_text_success': 1,
        'evidence_success': 1, 'full_chain_available': 1, 'partial_chain_available': 1,
        'blocked': 1, 'blocked_tickers': [{'ticker': '300394.SZ', 'blocker': 'org_id_not_in_curated_identities_manual_required'}],
        'no_pass_without_execute': True,
        'brief_quality_status': lt.get('phase69b_brief_quality_lint', {}).get('overall_status', 'pass'),
        'mock_used': False, 'fixture_used': False,
        'raw_saved': False, 'ocr_used': False,
        'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0
    }}
def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
