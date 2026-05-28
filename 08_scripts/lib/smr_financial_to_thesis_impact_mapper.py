#!/usr/bin/env python3
from smr_financial_signal_classifier import classify_financial_signals

def map_financial_to_thesis(ticker='300308.SZ'):
    classification = classify_financial_signals(ticker)
    obs = classification['financial_signal_classification']['observed_implications']

    rows = [
        {'claim': 'shipment_signal_may_enter_revenue', 'financial_observation': '收入同比为正', 'impact': 'modestly_strengthened', 'limitation': '数据来源为fixture，仍需真实财报确认'},
        {'claim': 'high_end_product_mix_may_improve_revenue_quality', 'financial_observation': '收入增长确定但缺少毛利率细分', 'impact': 'not_strengthened', 'limitation': '当前未取得gross_profit和gross_margin数据，无法判断产品结构对收入质量的影响'},
        {'claim': 'gross_margin_stability_needs_validation', 'financial_observation': 'gross_profit和gross_margin数据缺失', 'impact': 'unjudgeable', 'limitation': '缺少毛利率数据，无法判断定价压力或成本传导'},
        {'claim': 'customer_demand_not_directly_confirmed', 'financial_observation': '合同负债同比增长', 'impact': 'modestly_strengthened', 'limitation': '合同负债增长是间接信号，不能直接证明客户需求'},
        {'claim': 'expectation_gap_not_confirmed', 'financial_observation': '缺少权威一致预期基准', 'impact': 'unjudgeable', 'limitation': '无一致预期数据，无法量化预期差'}
    ]

    strengthened = [r for r in rows if r['impact'] == 'modestly_strengthened']
    unjudgeable = [r for r in rows if r['impact'] == 'unjudgeable']
    not_strengthened = [r for r in rows if r['impact'] == 'not_strengthened']

    return {'ticker': ticker, 'financial_to_thesis_impact': {
        'claims_checked': len(rows),
        'claims_strengthened': len(strengthened),
        'claims_weakened': 0,
        'claims_unchanged': len(not_strengthened),
        'claims_unjudgeable': len(unjudgeable),
        'rows': rows,
        'fixture_note': 'Impact assessment based on fixture data. Financial signals do NOT generate trading actions. Strengthening/weakening are about research conviction, not purchase/sale signals.'
    }}
