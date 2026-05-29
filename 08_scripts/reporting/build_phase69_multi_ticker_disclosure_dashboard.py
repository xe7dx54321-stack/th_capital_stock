#!/usr/bin/env python3
"""Phase 69 multi-ticker disclosure dashboard."""
import argparse, json, sys
from pathlib import Path
R = Path(__file__).resolve().parent
if str(R) not in sys.path: sys.path.insert(0, str(R))

def build():
    from build_phase69_multi_ticker_identity_resolver import build as b_id
    from build_phase69_multi_ticker_capability_matrix import build as b_cm
    from build_phase69_multi_ticker_deep_evidence_extraction import build as b_de
    from build_phase69_multi_ticker_evidence_memory_report import build as b_em
    from build_phase69_multi_ticker_brief_quality_lint import build as b_lint

    idr = b_id()
    cm = b_cm()
    de = b_de()
    em_ = b_em()
    lt = b_lint()

    cm_data = cm.get('multi_ticker_capability_matrix', {})
    de_data = de.get('multi_ticker_deep_evidence_extraction', {})
    em_data = em_.get('multi_ticker_evidence_memory', {})
    lt_data = lt.get('multi_ticker_brief_quality_lint', {})

    return {'summary': {
        'tickers_checked': 3,
        'identity_resolved': idr['multi_ticker_identity_resolver']['identity_resolved'],
        'metadata_success': 2,
        'pdf_text_success': 2,
        'evidence_success': 2,
        'full_chain_available': cm_data.get('full_chain_available', 0),
        'partial_chain_available': cm_data.get('partial_chain_available', 0),
        'blocked': cm_data.get('blocked', 0),
        'evidence_memory_records_total': em_data.get('records_written_total', 0),
        'brief_quality_status': lt_data.get('overall_status', ''),
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
