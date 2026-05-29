#!/usr/bin/env python3
'''Claim state memory.'''
from datetime import datetime, timezone
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

def build_claim_state(claim_linkage_rows: list[dict]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    rows = []
    newly_supported = 0
    still_unconfirmed = 0
    risk = 0

    for cl in claim_linkage_rows:
        name = cl.get('claim_name', '')
        status = cl.get('claim_status', 'unconfirmed')

        if status == 'supported' or status == 'partially_supported':
            delta = 'newly_supported'
            newly_supported += 1
        elif status == 'unconfirmed':
            delta = 'still_unconfirmed'
            still_unconfirmed += 1
        elif status == 'review_required':
            delta = 'review_required'
        else:
            delta = 'unchanged'

        rows.append({
            'claim_id': cl.get('claim_id', ''),
            'claim_name': name,
            'current_status': status,
            'previous_status': 'unconfirmed',
            'status_delta': delta,
            'supporting_evidence_count': cl.get('supporting_evidence_count', 0),
            'last_strengthened_phase': 'phase67b' if delta == 'newly_supported' else 'none',
            'last_updated_at': now,
            'limitation': cl.get('claim_limitation', ''),
            'cannot_conclude': cl.get('cannot_conclude', []),
            'next_possible_evidence_needed': _next_evidence(name)
        })

    return {
        'claims_total': len(rows),
        'newly_supported': newly_supported,
        'still_unconfirmed': still_unconfirmed,
        'risk_present': risk,
        'rows': rows
    }

def _next_evidence(claim: str) -> str:
    needs = {
        '800G_signal_supported': '收入拆分、出货量或客户分配的具体披露',
        '1_6T_signal_supported': '量产时间、收入贡献或客户认证进展的披露',
        'product_mix_partially_supported': '产品级收入占比或毛利率的披露',
        'shipment_delivery_supported': '具体出货量或ASP的披露',
        'customer_demand_proxy_supported': '客户份额或具体客户关系的披露',
        'order_visibility_partially_supported': '订单金额或具体客户的披露',
        'asp_trend_unconfirmed': '产品ASP趋势或定价策略的明确披露',
        'capacity_expansion_supported': '产能释放节奏或产能利用率的披露',
        'customer_share_unconfirmed': '客户集中度或重大合同公告',
        'specific_order_volume_unconfirmed': '具体订单金额或重大合同公告',
    }
    return needs.get(claim, '进一步披露或行业跟踪数据')
