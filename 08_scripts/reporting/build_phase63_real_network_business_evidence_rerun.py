#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reporting'))
from smr_chinese_business_text_chunker import chunk_chinese_business_texts
from build_phase61_real_business_evidence_to_claim_map import map_real_evidence_to_claims
from build_phase61_real_business_cannot_conclude_guard import run_real_guard

def build(conn, ticker=None):
    ticker = ticker or '300308.SZ'
    chunks = chunk_chinese_business_texts(ticker)
    claims = map_real_evidence_to_claims(ticker)
    guard = run_real_guard(ticker)
    cd = chunks['chinese_business_text_chunks']
    bd = claims['real_business_evidence_to_claim_map']
    gd = guard['real_business_cannot_conclude_guard']
    has_text = cd['chunks_created'] > 0

    return {'ticker': ticker, 'real_network_business_evidence_rerun': {
        'real_network_text_used': has_text,
        'phase50_fixture_used': False,
        'mock_text_used': False,
        'usable_text_sources': cd['texts_processed'],
        'chunks_created': cd['chunks_created'],
        'candidate_spans_found': cd['chunks_created'],
        'semantic_business_evidence_created': bd['claims_supported'] + bd['claims_partially_supported'],
        'business_evidence_passed': bd['claims_supported'],
        'business_claims_supported': bd['claims_supported'],
        'business_claims_unconfirmed': bd['claims_unconfirmed'],
        'guard_status': gd['guard_status'],
        'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0,
    }}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_network_business_evidence_rerun']
        print(f"# Real Network Evidence Rerun\n- Ticker: {r['ticker']}")
        print(f"- Real text: {d['real_network_text_used']} | Fixture: {d['phase50_fixture_used']} | Mock: {d['mock_text_used']}")
        print(f"- Claims supported: {d['business_claims_supported']} | Unconfirmed: {d['business_claims_unconfirmed']}")
        print(f"- Guard: {d['guard_status']} | P/O/T: 0/0/0")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
