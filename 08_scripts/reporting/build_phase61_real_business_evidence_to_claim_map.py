#!/usr/bin/env python3
"""Phase 61: Real Business Evidence to Claim Map.
Maps real-text business evidence to investment logic claims.
"""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from build_phase61_semantic_business_evidence_from_real_text import extract_semantic_from_real_text
from build_phase61_real_business_evidence_quality_gate import run_real_quality_gate

CLAIM_VARIABLE_MAP = {
    '800G_signal_supported': '800G_product_signal',
    '1_6T_signal_supported': '1_6T_product_signal',
    'high_end_product_mix_partially_supported': 'high_end_product_mix',
    'shipment_delivery_supported': 'shipment_delivery_signal',
    'order_visibility_partially_supported': 'order_visibility_signal',
    'customer_demand_proxy_supported': 'customer_demand_signal',
    'asp_trend_unconfirmed': 'asp_price_signal',
    'customer_share_unconfirmed': 'customer_demand_signal',
    'specific_order_volume_unconfirmed': 'order_visibility_signal',
}

def map_real_evidence_to_claims(ticker='300308.SZ'):
    evidence = extract_semantic_from_real_text(ticker)
    qg = run_real_quality_gate(ticker)
    qg_map = {r['evidence_id']: r for r in qg['real_business_evidence_quality_gate']['rows']}
    ev_rows = evidence['semantic_business_evidence_from_real_text']['rows']

    claims = {}
    for ev in ev_rows:
        qg_status = qg_map.get(ev['evidence_id'], {}).get('quality_status', 'rejected')
        if qg_status != 'passed':
            continue

        var = ev['business_variable']
        for claim_name, claim_var in CLAIM_VARIABLE_MAP.items():
            if claim_var == var:
                if claim_name not in claims:
                    claims[claim_name] = {'count': 0, 'strengths': {}}
                claims[claim_name]['count'] += 1
                claims[claim_name]['strengths'][ev['evidence_strength']] = \
                    claims[claim_name]['strengths'].get(ev['evidence_strength'], 0) + 1

    rows = []; supported = 0; partial = 0; unconfirmed = 0
    LIMITATIONS = {
        '800G_signal_supported': '真实材料支持800G相关进展，但不能确认800G收入占比。',
        '1_6T_signal_supported': '真实材料提到1.6T，支持产品方向存在进展，但不能确认大规模放量。',
        'high_end_product_mix_partially_supported': '高端产品结构方向偏正向，但不能拆分具体产品级毛利率。',
        'shipment_delivery_supported': '出货/交付口径积极，但不能确认具体出货量。',
        'order_visibility_partially_supported': '订单能见度表述积极，但不能确认具体订单金额。',
        'customer_demand_proxy_supported': '客户需求口径积极，但不能确认客户份额。',
        'asp_trend_unconfirmed': 'ASP/价格无直接证据。',
        'customer_share_unconfirmed': '客户份额仍无直接证据。',
        'specific_order_volume_unconfirmed': '具体订单量无直接证据。',
    }

    for claim_name in CLAIM_VARIABLE_MAP:
        c = claims.get(claim_name, {'count': 0, 'strengths': {}})
        if 'unconfirmed' in claim_name:
            status = 'unconfirmed'; unconfirmed += 1
        elif c['count'] >= 2:
            status = 'supported'; supported += 1
        elif c['count'] == 1:
            status = 'partially_supported'; partial += 1
        else:
            status = 'unconfirmed'; unconfirmed += 1

        rows.append({
            'claim': claim_name, 'claim_status': status,
            'supporting_real_evidence_count': c['count'],
            'evidence_strength_mix': c['strengths'],
            'limitation': LIMITATIONS.get(claim_name, ''),
        })

    return {'ticker': ticker, 'real_business_evidence_to_claim_map': {
        'claims_checked': len(rows), 'claims_supported': supported,
        'claims_partially_supported': partial, 'claims_unconfirmed': unconfirmed,
        'mock_claim_support_used': False, 'fixture_claim_support_used': True,
        'note': 'Real text evidence to claim mapping. Unconfirmed claims retained explicitly.',
        'rows': rows,
    }}

def build(conn,t=None): return map_real_evidence_to_claims(t or '300308.SZ')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_business_evidence_to_claim_map']
        print(f"# Real Business Evidence to Claim Map\n- Ticker: {r['ticker']}")
        print(f"- Supported: {d['claims_supported']} | Partial: {d['claims_partially_supported']} | Unconfirmed: {d['claims_unconfirmed']}")
        print(f"- Mock support: {d['mock_claim_support_used']}")
        for c in d['rows']:
            print(f"  - {c['claim']}: {c['claim_status']} (ev: {c['supporting_real_evidence_count']})")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
