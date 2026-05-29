#!/usr/bin/env python3
from smr_refined_quarterly_financial_signal_calculator import calculate_refined_quarterly_signals


def interpret_financial_signals(ticker='300308.SZ'):
    result = calculate_refined_quarterly_signals(ticker)
    signals_data = result['refined_quarterly_financial_signals']
    all_signals = signals_data.get('all_signals', [])
    latest = signals_data.get('latest_period', 'unknown')

    # Group latest signals by direction
    latest_signals = [s for s in all_signals if s['period'] == latest]

    observations = []
    signal_map = {
        'single_quarter_revenue_yoy': ('最新单季度收入同比', 'revenue_growth_quality'),
        'single_quarter_net_profit_yoy': ('最新单季度净利润同比', 'profit_growth_quality'),
        'gross_margin': ('最新毛利率', 'gross_margin_stability'),
        'gross_margin_yoy_delta': ('毛利率同比变动', 'gross_margin_stability'),
        'net_margin': ('最新净利率', 'profit_growth_quality'),
        'operating_profit_margin': ('营业利润率', 'profit_growth_quality'),
        'operating_cash_flow_to_net_profit': ('经营现金流/净利润比', 'cash_conversion_quality'),
        'inventory_to_revenue': ('存货/收入比', 'inventory_pressure'),
        'accounts_receivable_to_revenue': ('应收账款/收入比', 'receivable_pressure'),
        'contract_liabilities_yoy': ('合同负债同比', 'contract_liability_signal'),
        'capex_yoy': ('资本开支同比', 'capex_intensity'),
        'capex_to_revenue': ('资本开支/收入比', 'capex_intensity'),
    }

    for s in latest_signals:
        key = s['signal']
        info = signal_map.get(key)
        if info:
            label, dim = info
            if s['direction'] == 'positive':
                implication = f"{label}表现正面，对应维度{''.join(dim)}信号积极"
            elif s['direction'] == 'negative':
                implication = f"{label}表现偏弱，对应维度{''.join(dim)}需要持续观察"
            else:
                implication = f"{label}变化中性，对应维度{''.join(dim)}未给出明确方向"
            observations.append({
                'metric': key,
                'label': label,
                'dimension': dim,
                'period': s['period'],
                'value': s['value'],
                'direction': s['direction'],
                'observation': f"{label}为{'+' if s['direction']=='positive' else ('-' if s['direction']=='negative' else '~')}{s['value']}",
                'implication': implication,
                'confidence': s['confidence'],
            })

    positive_count = sum(1 for s in latest_signals if s['direction'] == 'positive')
    negative_count = sum(1 for s in latest_signals if s['direction'] == 'negative')

    if positive_count > negative_count + 1:
        overall = 'positive_bias'
    elif negative_count > positive_count + 1:
        overall = 'negative_bias'
    else:
        overall = 'mixed'

    return {
        'ticker': ticker,
        'financial_signal_interpretation': {
            'latest_period': latest,
            'observations': observations,
            'overall_interpretation': overall,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'missing_signals': signals_data.get('missing_reasons', {}),
            'confidence': 'real_structured',
        }
    }
