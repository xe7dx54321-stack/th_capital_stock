#!/usr/bin/env python3
'''Evidence-to-claim linkage memory.'''
from typing import Any

VARIABLE_TO_CLAIM = {
    '800G_product_signal': '800G_signal_supported',
    '1_6T_product_signal': '1_6T_signal_supported',
    'high_end_product_mix': 'product_mix_partially_supported',
    'shipment_delivery_signal': 'shipment_delivery_supported',
    'customer_demand_signal': 'customer_demand_proxy_supported',
    'order_visibility_signal': 'order_visibility_partially_supported',
    'asp_price_signal': 'asp_trend_unconfirmed',
    'capacity_expansion_signal': 'capacity_expansion_supported',
}

UNCONFIRMED_CLAIMS = ['customer_share_unconfirmed', 'specific_order_volume_unconfirmed']

def build_claim_linkage(evidence_records: list[dict]) -> dict[str, Any]:
    claim_map = {}
    for ev in evidence_records:
        var = ev.get('business_variable', '')
        claim_name = VARIABLE_TO_CLAIM.get(var, var)
        if claim_name not in claim_map:
            claim_map[claim_name] = {'eids': [], 'strengths': []}
        claim_map[claim_name]['eids'].append(ev.get('evidence_id', ''))
        claim_map[claim_name]['strengths'].append(ev.get('evidence_strength', ''))

    rows = []
    supported = 0
    for claim_name, data in claim_map.items():
        has_review = any('review_required' in s for s in data['strengths'])
        if 'unconfirmed' in claim_name:
            status = 'unconfirmed'
        elif has_review:
            status = 'review_required'
        else:
            status = 'supported'
            supported += 1

        limitation = _get_limitation(claim_name)
        rows.append({
            'claim_id': f'claim_{claim_name}',
            'claim_name': claim_name,
            'claim_status': status,
            'evidence_ids': data['eids'],
            'supporting_evidence_count': len(data['eids']),
            'new_evidence_count': len(data['eids']),
            'evidence_strength_mix': list(set(data['strengths'])),
            'claim_limitation': limitation,
            'cannot_conclude': _get_cannot_conclude(claim_name),
            'last_updated_phase': 'phase67b'
        })

    for uc in UNCONFIRMED_CLAIMS:
        if uc not in [r['claim_name'] for r in rows]:
            rows.append({
                'claim_id': f'claim_{uc}',
                'claim_name': uc,
                'claim_status': 'unconfirmed',
                'evidence_ids': [],
                'supporting_evidence_count': 0,
                'new_evidence_count': 0,
                'evidence_strength_mix': [],
                'claim_limitation': _get_limitation(uc),
                'cannot_conclude': _get_cannot_conclude(uc),
                'last_updated_phase': 'phase67b'
            })

    total_linked = sum(len(r['evidence_ids']) for r in rows)
    return {
        'claims_checked': len(rows),
        'claims_supported': supported,
        'claims_unconfirmed': sum(1 for r in rows if r['claim_status'] == 'unconfirmed'),
        'evidence_linkage_records': len(rows),
        'total_linked_evidence': total_linked,
        'rows': rows
    }

def _get_limitation(claim: str) -> str:
    lims = {
        '800G_signal_supported': '支持800G相关产品进展，但不确认800G收入占比、出货量或客户分配。',
        '1_6T_signal_supported': '支持1.6T相关产品进展，但不确认大规模放量、量产状态或收入贡献。',
        'product_mix_partially_supported': '支持产品结构升级方向，但不确认具体产品级收入占比。',
        'shipment_delivery_supported': '支持出货和交付积极表述，但不确认具体出货量或ASP。',
        'customer_demand_proxy_supported': '支持客户需求积极表述，但不确认客户份额或具体关系。',
        'order_visibility_partially_supported': '支持订单能见度表述，但不确认具体订单金额或客户。',
        'asp_trend_unconfirmed': 'ASP相关信息均标为review_required，不得直接确认ASP趋势。',
        'capacity_expansion_supported': '支持产能扩张表述，但不确认释放节奏或订单匹配。',
        'customer_share_unconfirmed': '无直接证据确认客户份额或NVIDIA分配。',
        'specific_order_volume_unconfirmed': '无直接证据确认具体订单量或金额。',
    }
    return lims.get(claim, '需要进一步人工审阅。')

def _get_cannot_conclude(claim: str) -> list[str]:
    cc = {
        '800G_signal_supported': ['800G revenue share', 'specific customer allocation', 'exact shipment volume'],
        '1_6T_signal_supported': ['1.6T mass production timing', '1.6T revenue contribution'],
        'product_mix_partially_supported': ['product-level revenue share', 'product-level gross margin'],
        'shipment_delivery_supported': ['specific shipment volume', 'specific ASP'],
        'customer_demand_proxy_supported': ['specific customer share', 'NVIDIA allocation'],
        'order_visibility_partially_supported': ['specific order amount', 'specific order volume'],
        'asp_trend_unconfirmed': ['ASP trend direction', 'ASP by product generation'],
        'capacity_expansion_supported': ['capacity release pace', 'order-to-capacity match'],
        'customer_share_unconfirmed': ['customer share percentage', 'specific customer relationship'],
        'specific_order_volume_unconfirmed': ['specific order volume', 'specific order amount'],
    }
    return cc.get(claim, ['insufficient evidence'])
