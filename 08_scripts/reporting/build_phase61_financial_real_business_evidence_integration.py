#!/usr/bin/env python3
"""Phase 61: Financial + Real Business Evidence Integration.
Merges Phase 59 real financial signals with Phase 61 real business evidence.
"""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from build_phase61_real_business_evidence_to_claim_map import map_real_evidence_to_claims
from smr_finance_aware_thesis_review import run_finance_aware_thesis_review
from smr_financial_business_evidence_integrator import integrate_financial_business_evidence

def integrate_financial_real_business(ticker='300308.SZ'):
    real_biz = map_real_evidence_to_claims(ticker)
    financial = run_finance_aware_thesis_review(ticker)

    b_rows = {r['claim']: r for r in real_biz['real_business_evidence_to_claim_map']['rows']}
    f_rows = {r['claim']: r for r in financial['finance_aware_thesis_review']['rows']}

    JOINT_CLAIMS = [
        ('revenue_realization_joint', '800G_signal_supported', 'business_momentum'),
        ('product_mix_joint', 'high_end_product_mix_partially_supported', 'margin_resilience'),
        ('shipment_revenue_joint', 'shipment_delivery_supported', 'revenue_realization'),
        ('order_visibility_joint', 'order_visibility_partially_supported', 'order_visibility_proxy'),
        ('customer_share_joint', 'customer_demand_proxy_supported', 'customer_share_unconfirmed'),
        ('asp_trend_joint', 'asp_trend_unconfirmed', 'asp_trend_unconfirmed'),
        ('expectation_gap_joint', None, 'expectation_gap_unconfirmed'),
    ]

    result_rows = []
    for joint_name, b_claim, f_claim in JOINT_CLAIMS:
        b_status = b_rows.get(b_claim, {}).get('claim_status', 'unconfirmed') if b_claim else 'unconfirmed'
        f_status = f_rows.get(f_claim, {}).get('review_result', 'unconfirmed') if f_claim else 'unconfirmed'

        if b_status == 'supported' and f_status == 'strengthened':
            joint = 'strengthened'
        elif b_status == 'supported' or f_status == 'strengthened':
            joint = 'partially_supported'
        elif b_status == 'partially_supported' or f_status == 'partially_supported':
            joint = 'partially_supported'
        elif 'unconfirmed' in b_status or 'unconfirmed' in f_status:
            joint = 'unconfirmed'
        else:
            joint = 'partially_supported'

        result_rows.append({
            'joint_claim': joint_name,
            'financial_side': f'财务侧判断: {f_status}',
            'business_side': f'业务侧判断(真实文本): {b_status}',
            'joint_assessment': joint,
            'limitation': '不能仅凭单侧证据确认整体判断。业务证据基于Phase 50 fixture真实文本。',
        })

    strengthened = sum(1 for r in result_rows if r['joint_assessment'] == 'strengthened')
    partial = sum(1 for r in result_rows if r['joint_assessment'] == 'partially_supported')
    unconfirmed = sum(1 for r in result_rows if r['joint_assessment'] == 'unconfirmed')

    return {'ticker': ticker, 'financial_real_business_evidence_integration': {
        'joint_claims_checked': len(result_rows),
        'joint_claims_strengthened': strengthened,
        'joint_claims_partially_supported': partial,
        'joint_claims_unconfirmed': unconfirmed,
        'real_business_evidence_used': True,
        'mock_business_evidence_used': False,
        'note': 'Financial + real business evidence integration using Phase 50 fixture text.',
        'rows': result_rows,
    }}

def build(conn,t=None): return integrate_financial_real_business(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['financial_real_business_evidence_integration']
        print(f"# Financial + Real Business Evidence Integration\n- Ticker: {r['ticker']}")
        print(f"- Strengthened: {d['joint_claims_strengthened']} | Partial: {d['joint_claims_partially_supported']} | Unconfirmed: {d['joint_claims_unconfirmed']}")
        print(f"- Real biz used: {d['real_business_evidence_used']} | Mock: {d['mock_business_evidence_used']}")
        for j in d['rows']:
            print(f"  - {j['joint_claim']}: {j['joint_assessment']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
