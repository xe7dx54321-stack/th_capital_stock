#!/usr/bin/env python3
from smr_watchlist_financial_delta_detector import detect_watchlist_financial_delta


THESIS_DIMENSIONS = [
    'business_momentum',
    'revenue_realization',
    'profit_quality',
    'margin_resilience',
    'cash_conversion',
    'order_visibility_proxy',
    'customer_share_unconfirmed',
    'asp_trend_unconfirmed',
    'expectation_gap_unconfirmed',
]

VARIABLE_TO_DIMENSION = {
    'shipment_revenue_conversion': ['business_momentum', 'revenue_realization'],
    'high_end_product_mix_signal': ['business_momentum', 'margin_resilience'],
    'margin_resilience': ['margin_resilience', 'profit_quality'],
    'order_visibility_financial_proxy': ['order_visibility_proxy'],
    'customer_demand_financial_proxy': ['customer_share_unconfirmed'],
    'capacity_preparation_signal': ['business_momentum'],
}


def run_finance_aware_thesis_review(ticker='300308.SZ'):
    delta = detect_watchlist_financial_delta(ticker)
    delta_rows = delta['watchlist_financial_delta']['rows']

    # Aggregate variable changes into thesis dimensions
    dimension_impact = {}
    for r in delta_rows:
        dims = VARIABLE_TO_DIMENSION.get(r['industry_variable'], [])
        if r['delta'] in ('strengthened',):
            for d in dims:
                dimension_impact[d] = max(dimension_impact.get(d, 0), 2)  # 2=strengthened
        elif r['delta'] in ('newly_observable',):
            for d in dims:
                dimension_impact[d] = max(dimension_impact.get(d, 0), 1)  # 1=partial
        elif r['delta'] in ('weakened',):
            dimension_impact[d] = min(dimension_impact.get(d, 0), -1)  # -1=weakened

    # Default: dimensions not mapped stay unconfirmed
    for dim in THESIS_DIMENSIONS:
        if dim not in dimension_impact:
            dimension_impact[dim] = 0  # 0=unconfirmed

    rows = []
    for dim in THESIS_DIMENSIONS:
        impact = dimension_impact.get(dim, 0)
        if impact >= 2:
            result = 'strengthened'
        elif impact == 1:
            result = 'partially_supported'
        elif impact <= -1:
            result = 'weakened'
        elif 'unconfirmed' in dim:
            result = 'unconfirmed'
        else:
            result = 'unchanged'

        evidence_map = {
            'business_momentum': '收入和利润端真实数据明显增强',
            'revenue_realization': '收入兑现增强',
            'profit_quality': '利润质量从毛利率和现金流角度获得支持',
            'margin_resilience': '毛利率处于较强水平',
            'cash_conversion': '现金流/净利润比可观察',
            'order_visibility_proxy': '存货和合同负债可观察但无法直接拆出订单',
            'customer_share_unconfirmed': '客户维度无法从财务数据直接确认',
            'asp_trend_unconfirmed': 'ASP无法从财务数据直接确认',
            'expectation_gap_unconfirmed': '预期差缺少市场一致预期数据',
        }
        limitation_map = {
            'business_momentum': '不能直接拆出具体产品代际贡献',
            'revenue_realization': '不能确认800G/1.6T具体占比',
            'profit_quality': '不能确认产品级利润贡献',
            'margin_resilience': '不能确认ASP改善或产品级价格趋势',
            'cash_conversion': '单季度可能有季节性现金效应',
            'order_visibility_proxy': '存货和合同负债不能等于订单确认',
            'customer_share_unconfirmed': '缺少客户份额相关数据',
            'asp_trend_unconfirmed': '缺少产品价格和产品级毛利率数据',
            'expectation_gap_unconfirmed': '缺少权威一致预期数据',
        }

        rows.append({
            'claim': dim,
            'review_result': result,
            'evidence': evidence_map.get(dim, ''),
            'meaning': evidence_map.get(dim, ''),
            'limitation': limitation_map.get(dim, ''),
        })

    strengthened = sum(1 for r in rows if r['review_result'] == 'strengthened')
    unconfirmed = sum(1 for r in rows if r['review_result'] == 'unconfirmed')

    if strengthened >= 3 and unconfirmed >= 2:
        overall = 'financials_strengthen_business_momentum_but_do_not_close_key_gaps'
    elif strengthened >= 2:
        overall = 'financials_partially_strengthen_some_claims'
    else:
        overall = 'financials_mixed_or_inconclusive'

    return {
        'ticker': ticker,
        'finance_aware_thesis_review': {
            'overall_review': overall,
            'claims_checked': len(rows),
            'claims_strengthened': strengthened,
            'claims_weakened': sum(1 for r in rows if r['review_result'] == 'weakened'),
            'claims_unchanged': sum(1 for r in rows if r['review_result'] == 'unchanged'),
            'claims_unconfirmed': unconfirmed,
            'rows': rows,
            'pending_allowed': False,
            'paper_order_allowed': False,
            'real_trade_allowed': False,
        }
    }
