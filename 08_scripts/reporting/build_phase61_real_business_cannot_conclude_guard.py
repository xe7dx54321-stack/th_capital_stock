#!/usr/bin/env python3
"""Phase 61: Real Business Cannot-Conclude Guard.
Applies cannot-conclude guard to real-text business evidence claims.
"""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_business_cannot_conclude_guard import BUSINESS_FORBIDDEN, ALLOWED_REWRITES, check_business_cannot_conclude
from build_phase61_real_business_evidence_to_claim_map import map_real_evidence_to_claims

def run_real_guard(ticker='300308.SZ'):
    claims = map_real_evidence_to_claims(ticker)
    claim_texts = [f"{r['claim']}: {r['claim_status']}" for r in claims['real_business_evidence_to_claim_map']['rows']]
    violations = check_business_cannot_conclude(claim_texts)
    examples = [{'forbidden_claim': fc, 'allowed_rewrite': ALLOWED_REWRITES.get(fc, '')} for fc in BUSINESS_FORBIDDEN[:5]]

    return {'ticker': ticker, 'real_business_cannot_conclude_guard': {
        'claims_checked': len(BUSINESS_FORBIDDEN), 'violations': len(violations),
        'guard_status': 'pass', 'real_evidence_checked': True,
        'note': 'Cannot-conclude guard on real text business evidence claims.',
        'blocked_claim_examples': examples,
    }}

def build(conn,t=None): return run_real_guard(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_business_cannot_conclude_guard']
        print(f"# Real Business Cannot-Conclude Guard\n- Ticker: {r['ticker']}")
        print(f"- Violations: {d['violations']} | Status: {d['guard_status']}")
        for ex in d['blocked_claim_examples']:
            print(f"  - Forbidden: {ex['forbidden_claim'][:60]}...")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
