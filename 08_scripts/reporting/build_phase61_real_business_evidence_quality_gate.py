#!/usr/bin/env python3
"""Phase 61: Real Business Evidence Quality Gate.
Runs quality gate on real-text-based business evidence.
Reuses Phase 60 quality gate logic with real text evidence input.
"""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from build_phase61_semantic_business_evidence_from_real_text import extract_semantic_from_real_text
from smr_business_evidence_quality_gate import GENERIC_PHRASES, TITLE_ONLY_INDICATORS

def run_real_quality_gate(ticker='300308.SZ'):
    evidence = extract_semantic_from_real_text(ticker)
    rows = evidence['semantic_business_evidence_from_real_text']['rows']

    qg_rows = []; passed = 0; review = 0; rejected = 0

    for ev in rows:
        span = ev['quoted_span']; issues = []
        if not ev.get('source_id'): issues.append('no_source_traceability')
        if len(span) < 10: issues.append('quoted_span_too_short')
        is_title = any(ind in span[:4] for ind in TITLE_ONLY_INDICATORS)
        if is_title: issues.append('appears_title_only')
        if any(gp in span for gp in GENERIC_PHRASES) and len(span) < 30: issues.append('potentially_generic_language')

        if 'no_source_traceability' in issues or 'quoted_span_too_short' in issues:
            quality_status = 'rejected'; rejected += 1
        elif ev.get('sensitive_variable') and ev.get('evidence_strength') != 'strong_direct_evidence':
            quality_status = 'review_required'; review += 1
        elif issues:
            quality_status = 'review_required'; review += 1
        else:
            quality_status = 'passed'; passed += 1

        qg_rows.append({
            'evidence_id': ev['evidence_id'], 'quality_status': quality_status, 'issues': issues,
            'allowed_usage': (
                'business_judgment_support' if quality_status == 'passed'
                else 'limited_reference_only' if quality_status == 'review_required'
                else 'not_allowed'
            ),
            'blocked_usages': [
                'confirmed_customer_share', 'confirmed_ASP',
                'confirmed_order_volume', 'confirmed_product_revenue_share'
            ] if ev.get('sensitive_variable') else [],
        })

    return {'ticker': ticker, 'real_business_evidence_quality_gate': {
        'evidence_checked': len(rows), 'passed': passed,
        'review_required': review, 'rejected': rejected,
        'mock_evidence_used': False, 'fixture_evidence_used': True,
        'note': 'Quality gate on real-text evidence. Sensitive variables flagged for review.',
        'rows': qg_rows,
    }}

def build(conn,t=None): return run_real_quality_gate(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_business_evidence_quality_gate']
        print(f"# Real Business Evidence Quality Gate\n- Ticker: {r['ticker']}")
        print(f"- Passed: {d['passed']} | Review: {d['review_required']} | Rejected: {d['rejected']}")
        for g in d['rows'][:5]:
            print(f"  - {g['evidence_id']}: {g['quality_status']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
