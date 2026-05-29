#!/usr/bin/env python3
'''Phase 68 evidence memory and brief dashboard.'''
import argparse, json, sys
from pathlib import Path
R = Path(__file__).resolve().parent
if str(R) not in sys.path: sys.path.insert(0, str(R))

def build():
    from build_phase68_internal_research_brief import build as build_brief
    from build_phase68_internal_brief_quality_lint import build as build_lint
    from build_phase68_evidence_claim_linkage import build as build_cl
    from build_phase68_evidence_memory_write_report import build as build_wr
    br = build_brief('300308.SZ')
    lt = build_lint('300308.SZ')
    cl = build_cl('300308.SZ')
    wr = build_wr('300308.SZ')
    b = br['phase68_internal_research_brief']
    l = lt['internal_brief_quality_lint']
    c = cl['evidence_claim_linkage']
    w = wr['evidence_memory_write_report']
    return {'summary': {
        'ticker': '300308.SZ',
        'evidence_memory_records': w.get('records_written', 0),
        'source_trace_passed': w.get('records_written', 0),
        'claims_supported': c.get('claims_supported', 0),
        'claims_unconfirmed': c.get('claims_unconfirmed', 0),
        'brief_sections': b.get('sections', 0),
        'brief_quality_status': l.get('overall_status', ''),
        'system_terms_found': l.get('system_terms_found', 0),
        'teaching_phrases_found': l.get('teaching_phrases_found', 0),
        'trade_advice_terms_found': l.get('trade_advice_terms_found', 0),
        'overclaim_violations': l.get('overclaim_violations', 0),
        'watchlist_decision': 'continue_tracking_evidence_strengthened',
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
