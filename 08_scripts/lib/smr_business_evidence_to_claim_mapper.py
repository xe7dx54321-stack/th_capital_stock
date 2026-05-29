#!/usr/bin/env python3
from smr_semantic_business_evidence_extractor import extract_semantic_business_evidence

VARIABLE_TO_CLAIM = {
    '800G_product_signal': '800G_signal_supported',
    '1_6T_product_signal': '1_6T_signal_supported',
    'high_end_product_mix': 'high_end_product_mix_partially_supported',
    'shipment_delivery_signal': 'shipment_delivery_supported',
    'customer_demand_signal': 'customer_demand_proxy_supported',
    'asp_price_signal': 'asp_trend_unconfirmed',
    'order_visibility_signal': 'order_visibility_partially_supported',
}

def map_business_evidence_to_claims(ticker='300308.SZ'):
    evidence = extract_semantic_business_evidence(ticker)
    rows = evidence['semantic_business_evidence']['rows']

    # Group by variable
    by_var = {}
    for ev in rows:
        v = ev['business_variable']
        if v not in by_var:
            by_var[v] = {'rows': [], 'strengths': {}}
        by_var[v]['rows'].append(ev)
        s = ev['evidence_strength']
        by_var[v]['strengths'][s] = by_var[v]['strengths'].get(s, 0) + 1

    claim_rows = []
    for var_name, claim_name in VARIABLE_TO_CLAIM.items():
        var_data = by_var.get(var_name, {'rows': [], 'strengths': {}})
        evidence_count = len(var_data['rows'])
        strengths = var_data['strengths']

        # Determine claim status
        strong = strengths.get('strong_direct_evidence', 0)
        medium = strengths.get('medium_management_commentary', 0)

        if 'unconfirmed' in claim_name:
            claim_status = 'unconfirmed'
        elif strong >= 1 and medium >= 1:
            claim_status = 'supported'
        elif medium >= 2:
            claim_status = 'supported'
        elif medium == 1 or strong == 1:
            claim_status = 'partially_supported'
        elif evidence_count == 0:
            claim_status = 'unconfirmed'
        else:
            claim_status = 'partially_supported'

        limitations = {
            '800G_signal_supported': '不能直接确认800G收入占比。',
            '1_6T_signal_supported': '不能确认1.6T已大规模放量。',
            'high_end_product_mix_partially_supported': '不能拆分具体产品收入占比。',
            'shipment_delivery_supported': '不能确认具体出货量。',
            'customer_demand_proxy_supported': '不能确认客户份额。',
            'asp_trend_unconfirmed': '缺少ASP直接披露数据。',
            'order_visibility_partially_supported': '不能确认具体在手订单金额。',
        }

        claim_rows.append({
            'claim': claim_name,
            'claim_status': claim_status,
            'supporting_evidence_count': evidence_count,
            'evidence_strength_mix': strengths,
            'limitation': limitations.get(claim_name, '需要更多直接证据。'),
        })

    supported = sum(1 for r in claim_rows if r['claim_status'] == 'supported')
    partial = sum(1 for r in claim_rows if r['claim_status'] == 'partially_supported')
    unconfirmed = sum(1 for r in claim_rows if r['claim_status'] == 'unconfirmed')

    return {
        'ticker': ticker,
        'business_evidence_to_claim_map': {
            'claims_checked': len(claim_rows),
            'claims_supported': supported,
            'claims_partially_supported': partial,
            'claims_unconfirmed': unconfirmed,
            'note': 'Fixture-based claim mapping. Claims ending in _unconfirmed are set unconfirmed by design.',
            'rows': claim_rows,
        }
    }
