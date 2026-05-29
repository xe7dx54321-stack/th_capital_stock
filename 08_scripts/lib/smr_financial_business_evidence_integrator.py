#!/usr/bin/env python3
from smr_business_evidence_to_claim_mapper import map_business_evidence_to_claims
from smr_finance_aware_thesis_review import run_finance_aware_thesis_review


def integrate_financial_business_evidence(ticker='300308.SZ'):
    business = map_business_evidence_to_claims(ticker)
    financial = run_finance_aware_thesis_review(ticker)

    b_rows = {r['claim']: r for r in business['business_evidence_to_claim_map']['rows']}
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

        # Joint assessment
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

        b_summary = b_rows.get(b_claim, {}).get('claim_status', 'no_data') if b_claim else 'not_applicable'
        f_summary = f_rows.get(f_claim, {}).get('review_result', 'no_data') if f_claim else 'not_applicable'

        result_rows.append({
            'joint_claim': joint_name,
            'financial_side': f"财务侧判断: {f_summary}",
            'business_side': f"业务侧判断: {b_summary}",
            'joint_assessment': joint,
            'limitation': '不能仅凭单侧证据确认整体判断。联合判断受限于业务证据的可用性和财务数据的解释边界。',
        })

    strengthened = sum(1 for r in result_rows if r['joint_assessment'] == 'strengthened')
    partial = sum(1 for r in result_rows if r['joint_assessment'] == 'partially_supported')
    unconfirmed = sum(1 for r in result_rows if r['joint_assessment'] == 'unconfirmed')

    return {
        'ticker': ticker,
        'financial_business_evidence_integration': {
            'joint_claims_checked': len(result_rows),
            'joint_claims_strengthened': strengthened,
            'joint_claims_partially_supported': partial,
            'joint_claims_unconfirmed': unconfirmed,
            'note': 'Fixture-based joint assessment. Financial + business evidence combined with cannot-conclude guard.',
            'rows': result_rows,
        }
    }
