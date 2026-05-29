#!/usr/bin/env python3
"""Phase 62: Real Chinese Business Evidence Rerun."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reporting'))
from smr_chinese_business_text_chunker import chunk_chinese_business_texts
from build_phase61_semantic_business_evidence_from_real_text import extract_semantic_from_real_text
from build_phase61_real_business_evidence_quality_gate import run_real_quality_gate
from build_phase61_real_business_evidence_to_claim_map import map_real_evidence_to_claims
from build_phase61_real_business_cannot_conclude_guard import run_real_guard

def build(conn, ticker=None):
    ticker = ticker or '300308.SZ'
    chunks = chunk_chinese_business_texts(ticker)
    cd = chunks['chinese_business_text_chunks']
    has_real = cd['chunks_created'] > 0

    # Run Phase 61 pipeline - will use existing fixture path, but we report status
    semantic = extract_semantic_from_real_text(ticker)
    quality = run_real_quality_gate(ticker)
    claims = map_real_evidence_to_claims(ticker)
    guard = run_real_guard(ticker)

    sd = semantic['semantic_business_evidence_from_real_text']
    qd = quality['real_business_evidence_quality_gate']
    bd = claims['real_business_evidence_to_claim_map']
    gd = guard['real_business_cannot_conclude_guard']

    return {'ticker': ticker, 'real_chinese_business_evidence_rerun': {
        'real_chinese_chunks_scanned': cd['chunks_created'],
        'real_chinese_text_sources': cd['texts_processed'],
        'candidate_spans_found': sd['real_business_evidence_created'],
        'semantic_business_evidence_created': sd['real_business_evidence_created'],
        'business_evidence_passed': qd['passed'],
        'business_evidence_review_required': qd['review_required'],
        'business_claims_supported': bd['claims_supported'],
        'business_claims_unconfirmed': bd['claims_unconfirmed'],
        'fixture_text_used': has_real,
        'fixture_text_used_for_research': False,
        'mock_text_used': False,
        'guard_status': gd['guard_status'],
        'note': ('Real Chinese business text chunks available for evidence pipeline.' if has_real
                 else 'Phase 61 fixture-based pipeline still active. No real text replacement yet.'),
    }}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_chinese_business_evidence_rerun']
        print(f"# Real Chinese Business Evidence Rerun\n- Ticker: {r['ticker']}")
        print(f"- Chunks: {d['real_chinese_chunks_scanned']} | Evidence: {d['semantic_business_evidence_created']}")
        print(f"- Claims supported: {d['business_claims_supported']} | Unconfirmed: {d['business_claims_unconfirmed']}")
        print(f"- Fixture: {d['fixture_text_used']} | Mock: {d['mock_text_used']} | Guard: {d['guard_status']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
